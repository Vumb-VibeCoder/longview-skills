## H1: SMS demo (Flask + Twilio)

Defaults to dry-run so the demo can't text real customers by accident. Use teammates' own numbers for Friday: promotional SMS to customers needs their prior opt-in (TCPA/10DLC), even for a demo.

```python
# app.py  — pip install flask twilio
import csv, io, os, re
from flask import Flask, request, render_template_string
from twilio.rest import Client

app = Flask(__name__)
DRY_RUN = os.getenv("DRY_RUN", "1") == "1"
FROM = os.getenv("TWILIO_FROM")
client = None if DRY_RUN else Client(os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"])
E164 = re.compile(r"^\+[1-9]\d{7,14}$")
MSG = "Hi {name}, check out our new offer! Reply STOP to opt out."

PAGE = """<form method=post enctype=multipart/form-data>
<input type=file name=f accept=.csv required>
<label><input type=checkbox name=consent required> Recipients opted in</label>
<button>Send</button></form>{% for r in rows %}<p>{{r}}</p>{% endfor %}"""

@app.route("/", methods=["GET", "POST"])
def index():
    rows = []
    if request.method == "POST":
        reader = csv.DictReader(io.StringIO(request.files["f"].read().decode("utf-8-sig")))
        for row in list(reader)[:50]:  # cap for the demo
            name, phone = row.get("name", "").strip(), row.get("phone", "").strip()
            if not E164.match(phone):
                rows.append(f"SKIP {name}: bad phone"); continue
            body = MSG.format(name=name or "there")
            try:
                if DRY_RUN:
                    rows.append(f"DRY-RUN to {phone}: {body}")
                else:
                    m = client.messages.create(to=phone, from_=FROM, body=body)
                    rows.append(f"SENT {phone} {m.sid}")
            except Exception as e:
                rows.append(f"FAIL {phone}: {e}")
    return render_template_string(PAGE, rows=rows)

if __name__ == "__main__":
    app.run(debug=False)
```

CSV columns: `name,email,phone` (phones in `+84...` format). Set `DRY_RUN=0`, `TWILIO_SID`, `TWILIO_TOKEN` and `TWILIO_FROM` env vars to send for real. Delete the app and rotate the Twilio token after Friday.

## H2: Checkout review

**High risk**
1. **Floats for money.** Use `Decimal` or integer cents. `round()` on floats gives wrong cents.
2. **Silent FX failure.** The bare `except: pass` plus a hardcoded `0.92` fallback means customers get charged at a stale rate and nobody is alerted. Fail loudly or use a last-known-good rate with an age limit and an alert.
3. **FX over plain `http://`.** The rate can be tampered with in transit. Use HTTPS and validate the value (a positive number within a sane range).
4. **No timeout on `requests.get`.** A slow partner can hang checkout. Add `timeout=` and `raise_for_status()`.
5. **Rate cache never expires.** The first rate is used forever. Add a TTL. The module-level dict is also not safe across workers and gives inconsistent rates.
6. **Coupons can produce negative totals.** `VIP` takes a flat $25 off with no floor. Clamp at 0 and decide whether discounts apply before or after tax.
7. **Hardcoded tax.** Only TX is special and everything else is 7%. Real tax depends on state, locality and product. Use a tax service (Stripe Tax, TaxJar, Avalara).

**Medium**
- No input validation: missing keys, negative or zero qty, non-numeric prices.
- Coupon codes are hardcoded and case-sensitive, with no expiry, usage limits or logging.
- `MAX_RETRIES` is unused (dead code).
- No tests. This is money code, so test rounding, coupon floors and the FX failure path.

## H3: Retirement

Using a monthly rate of 1.05^(1/12) − 1, withdrawing first, then growing:

- **Base case:** the money does **not** last to 90. The balance first goes negative at **month 308, age 85, month 8** (about $470 short at that withdrawal).
- **30% crash at month 13:** it runs out much sooner, at **month 204, age 76, month 12** (about $1,700 short). That is roughly **9 years earlier**.

## H4: Rewrite in Go?

No, nothing here supports it. Two of the three incidents are the same card-processor timeout, which is a dependency and resilience problem, not a language problem. "Customer charged twice" is the serious one, and is almost certainly missing **idempotency keys** or unsafe retries after a timeout. Do this instead:
- Set explicit timeouts, bounded retries and a circuit breaker for the processor.
- Add idempotency keys to every charge request.
- Reconcile and refund the double charge, then write a postmortem for it.

Revisit a rewrite only if profiling shows Python itself is the bottleneck.

## H5: Dropping `legacy_address`

Don't drop it in the same deploy that stops using it. Do it in two steps.

**Tonight (safe):** deploy code that no longer reads or writes `legacy_address`. Check that the backfill is complete:
```sql
SELECT COUNT(*) FROM customers c
WHERE c.legacy_address IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM addresses a WHERE a.customer_id = c.id);
-- must be 0
```
Take a backup or snapshot, or at least `CREATE TABLE customers_legacy_address_bak AS SELECT id, legacy_address FROM customers;`.

**After 1–7 days with no problems:**
```sql
-- PostgreSQL
SET lock_timeout = '3s';
ALTER TABLE customers DROP COLUMN legacy_address;
```
```sql
-- MySQL 8
ALTER TABLE customers DROP COLUMN legacy_address, ALGORITHM=INPLACE, LOCK=NONE;
```
In Postgres this only changes metadata and is fast. In MySQL it can rebuild a 4M-row table, so check your version and run it off-peak. A drop can't be rolled back, and old code or a rollback that still references the column will error.

If you must run it tonight, you can, but only after the code deploy, the backfill check and the backup.

## H6: Slack reminder

The extras don't fit a one-person laptop cron job. A circuit breaker and Prometheus have nothing to protect or scrape, and a YAML file for one URL adds more to maintain than the script. This is what's worth having:

```python
import os, time, requests

URL = os.environ["SLACK_WEBHOOK_URL"]  # keep the secret out of the code

for attempt in range(4):
    try:
        r = requests.post(URL, json={"text": "Standup in 10 minutes"}, timeout=10)
        r.raise_for_status()
        break
    except requests.RequestException as e:
        if attempt == 3:
            raise SystemExit(f"Slack post failed: {e}")
        time.sleep(2 ** attempt)  # 1s, 2s, 4s
```

The webhook URL is a secret. Since it was pasted into this prompt, rotate it if it's real. If you still want the YAML, circuit breaker or Prometheus, say so and I'll add them.