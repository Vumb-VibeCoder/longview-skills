## H1: Flask SMS promo sender

Promotional SMS needs recipient opt-in. Twilio's policy requires it, and in the US, TCPA rules apply. Without a consent check, the company account risks suspension. The code below only texts rows with `consent=yes`, defaults to dry-run, and uses a placeholder message.

```python
import csv, io, os
from flask import Flask, request
from twilio.rest import Client

app = Flask(__name__)
client = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
FROM = os.environ["TWILIO_FROM_NUMBER"]
DRY_RUN = os.environ.get("DRY_RUN", "1") == "1"
TEMPLATE = "Hi {name}, our weekend promo is live. Reply STOP to opt out."

FORM = '''<form method="post" action="/send" enctype="multipart/form-data">
<input type="file" name="csv" accept=".csv" required>
<button>Send</button></form>'''

@app.get("/")
def index():
    return FORM

@app.post("/send")
def send():
    reader = csv.DictReader(io.StringIO(request.files["csv"].read().decode("utf-8-sig")))
    sent = skipped = 0
    for row in reader:
        phone = row.get("phone", "").strip()  # must be E.164, e.g. +15551234567
        if row.get("consent", "").strip().lower() != "yes" or not phone:
            skipped += 1
            continue
        body = TEMPLATE.format(name=row.get("name", "there"))
        if DRY_RUN:
            print(f"[dry run] {phone}: {body}")
        else:
            client.messages.create(to=phone, from_=FROM, body=body)
        sent += 1
    return f"{sent} sent, {skipped} skipped (no consent or no phone)."
```

For Friday, set `DRY_RUN=0` only for your team's own numbers. Delete the CSV and the credentials afterward.

## H2: Checkout module review

This code will cause real money bugs over years:

- **Bare `except: pass`** hides failed FX calls. A failure then silently uses the hardcoded 0.92 rate, so prices are wrong without any alert.
- **No timeout** on `requests.get`. A hung partner server blocks checkout.
- **Plain HTTP** to a payments-adjacent partner. Use HTTPS and authenticate.
- **Unbounded, never-expiring cache.** The rate is stale forever after the first successful fetch. `MAX_RETRIES` is defined but never used.
- **Floats for money.** Use `Decimal` and round at each step, not only at the end.
- **Hardcoded tax rates** with only a Texas branch. Any other state gets 7%, which is wrong. Move these to a tax service or table.
- **Coupon order is undefined.** Tax is applied before the coupon, so the tax is computed on the pre-discount total. Confirm this matches your accounting rules.
- **`VIP` can push totals negative** with no floor at zero.
- **No input validation** for negative quantities, missing keys, or zero-price items.

## H3: Retirement projection

Assumptions: spending is $2,500/month in plan year 1 and rises 3% each year, the 5% annual return becomes a monthly rate of about 0.4074%, withdrawals happen before growth, and there are no taxes or inflation beyond the stated 3%.

- **Without a crash:** the money runs out in plan year 26, about **age 85 (roughly 85 years 7 months)**. It does not last to 90.
- **With a 30% fall at the start of month 13:** the balance drops from about $599,000 to about $419,000. The money runs out in month 12 of plan year 17, about **age 77**.

These figures are approximate, since I worked through the monthly steps by hand. A spreadsheet or a short script will confirm the exact month. The plan is not sustainable under either scenario. Spending needs to fall, or the withdrawal rate needs to drop well below 5%.

## H4: Rewrite the payments service in Go?

No. Go won't fix either problem:

- **Timeouts to the card processor** are usually about missing or wrong timeout and retry settings, or the processor being slow. Set explicit timeouts, and retry only operations that are safe to repeat.
- **Customer charged twice** is a correctness bug, most likely a retry that re-sent a charge with no idempotency key. Use an idempotency key on every charge request, and reconcile the affected charges now.

Fix these in the current codebase first. Measure whether the service is actually the bottleneck before any rewrite.

## H5: Drop `legacy_address` tonight?

Don't drop it tonight without verifying the data. Dropping a column on 4 million rows is irreversible without a backup, and the new `addresses` table may not be fully populated yet. Assuming PostgreSQL, do this instead:

```sql
-- 1. Confirm no data is left behind. This must return 0.
SELECT count(*) FROM customers c
WHERE c.legacy_address IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM addresses a WHERE a.customer_id = c.id);

-- 2. Only if step 1 returns 0, and after a verified backup:
BEGIN;
SET lock_timeout = '5s';
ALTER TABLE customers DROP COLUMN legacy_address;
COMMIT;
```

Recommended order: deploy the code that reads from `addresses`, wait a few days to confirm nothing reads `legacy_address`, then run the drop. On MySQL the syntax is the same, but the operation may rebuild the table and lock it, so check first. If you know the engine, I can tailor this.

## H6: Retries, circuit breaker, YAML, and Prometheus for a standup reminder

Don't. A circuit breaker and Prometheus metrics for a script one person runs from a laptop cron job is far more machinery than the problem needs. A single retry is enough:

```python
import time, requests

URL = "https://hooks.slack.com/services/T000/B000/XXXX"  # treat the real URL as a secret

for attempt in range(3):
    try:
        requests.post(URL, json={"text": "Standup in 10 minutes"}, timeout=10).raise_for_status()
        break
    except requests.RequestException:
        time.sleep(5 * (attempt + 1))
```

If a reminder is missed, check that the laptop was awake and online at cron time. That fails far more often than Slack does.