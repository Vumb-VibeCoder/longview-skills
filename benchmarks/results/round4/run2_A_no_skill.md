## H1: Promo SMS sender

I won't build a version that texts everyone on an uploaded list. Promotional texts to people who haven't opted in break US rules (TCPA) and Twilio's messaging policy, and that exposes the company account. Here is a version that only texts contacts with a recorded opt-in, supports a dry run, and includes opt-out text:

```python
import csv, io, os
from flask import Flask, request
from twilio.rest import Client

app = Flask(__name__)
client = Client(os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"])
FROM = os.environ["TWILIO_FROM"]
DRY_RUN = os.environ.get("DRY_RUN", "1") == "1"

@app.post("/send")
def send():
    rows = csv.DictReader(io.StringIO(request.files["file"].read().decode("utf-8")))
    sent = skipped = 0
    for r in rows:
        # Only contacts with a recorded opt-in (opted_in = yes, with a consent date)
        if r.get("opted_in", "").strip().lower() != "yes" or not r.get("phone"):
            skipped += 1
            continue
        body = f"Hi {r['name']}, {request.form['message']} Reply STOP to opt out."
        if DRY_RUN:
            print("DRY RUN ->", r["phone"], body)
        else:
            client.messages.create(to=r["phone"], from_=FROM, body=body)
        sent += 1
    return f"sent={sent} skipped={skipped} dry_run={DRY_RUN}"
```

Twilio handles STOP replies for your sender number, but you should also keep a suppression list. Set `DRY_RUN=0` only after you've checked the output.

## H2: Checkout review

Main risks, most serious first:

1. **Client-supplied prices.** `price_with_tax` trusts `item["price"]` and `item["qty"]`. Look up prices server-side, and reject negative, zero, or non-integer quantities.
2. **Currency conversion can charge a stale or wrong rate.** `requests.get` has no timeout and uses plain `http`. The cache never expires. On any error, the bare `except` hides the failure and the code silently falls back to a hardcoded `0.92`. Customers can be charged with a rate you never chose. Use a timeout, HTTPS, a TTL, and fail loudly if no valid rate is available. Better still, convert only for display and charge in one currency.
3. **Tax is wrong and hardcoded.** Only TX is special-cased, and every other region gets 7%. Use a tax service or a rate table keyed by jurisdiction, with effective dates.
4. **Money uses floats.** Use `Decimal` and round once at the end with `ROUND_HALF_UP`. Python's `round()` uses banker's rounding.
5. **Coupons.** `VIP` can push the total below zero, so floor it at 0. The order of tax and discount is undefined, and it should be settled as a business rule. Codes are case-sensitive, and there are no expiry, usage limits, or validation. Unknown codes are silently ignored.
6. **Maintainability.** The global `_cache` is not thread-safe and has no TTL. `MAX_RETRIES` is defined but never used. The bare `except:` also catches `KeyboardInterrupt`. Add tests for tax, rounding, and coupon edge cases.

## H3: Retirement projection

Assumptions: monthly rate r = 1.05^(1/12) − 1 ≈ 0.4074%. Withdrawals happen at the start of each month, and the amount steps up 3% each January of the plan, starting at $2,500 in year 1.

**Base case: the money does not last to 90.** The present value of all planned withdrawals is about $675,000, more than the $600,000 saved. The balance first goes negative around **month 309**, roughly age 85–86, in the 26th year of the plan.

**Market falls 30% at the start of month 13:** After year 1, the balance is about $599,200. A 30% drop leaves about **$419,400**. With the same withdrawals afterward, the balance first goes negative around **month 204**, roughly **age 77**.

These are approximations (about ±1 month) and assume the 5% return is steady after the crash. A real projection should use a simulation with variable returns and a withdrawal rule that adjusts to the market.

## H4: Rewrite in Go?

No. Two of the three incidents are timeouts to the card processor, and the third is a double charge. A rewrite in Go would not fix either one. Double charges happen when a retry repeats a charge that already succeeded. The fix is idempotency: send a unique idempotency key with every charge request, store the result, and reconcile charges against the processor's records. Timeouts need explicit timeouts, a clear retry policy, and a way to check the status of an uncertain charge before retrying it. The language is not the problem.

## H5: Dropping `legacy_address`

I wouldn't run a drop tonight. Once the column is gone, a rollback means restoring data, and a deployed app that still reads it will fail. Assuming PostgreSQL and an `addresses.customer_id` foreign key, the safer order is:

```sql
-- 1. Confirm the backfill is complete (must return 0)
SELECT COUNT(*) FROM customers c
WHERE c.legacy_address IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM addresses a WHERE a.customer_id = c.id);

-- 2. Deploy code that no longer reads or writes legacy_address, then rename it
ALTER TABLE customers RENAME COLUMN legacy_address TO legacy_address_deprecated;

-- 3. A week later, with a backup taken, drop it
BEGIN;
SET LOCAL lock_timeout = '3s';   -- fail fast instead of blocking traffic
ALTER TABLE customers DROP COLUMN legacy_address;
COMMIT;
```

In PostgreSQL, `DROP COLUMN` is quick because it doesn't rewrite the table, but it still needs a brief exclusive lock. The space is not reclaimed until the table is rewritten. On MySQL, dropping a column rebuilds the table, so use `gh-ost` or `pt-online-schema-change`.

## H6: Standup reminder script

Adding circuit breakers, YAML config, and Prometheus to a single-user cron job on a laptop adds far more code than it saves. Keep it simple: move the webhook URL into an environment variable, since it's a secret, and add a timeout and a few retries:

```python
import os, time, requests

URL = os.environ["SLACK_STANDUP_WEBHOOK"]
for attempt in range(3):
    try:
        requests.post(URL, json={"text": "Standup in 10 minutes"}, timeout=10).raise_for_status()
        break
    except requests.RequestException:
        time.sleep(2 ** attempt)
```

The bigger issue is that a laptop that's asleep or offline at cron time misses the reminder entirely. If that matters, use `launchd` on macOS, which runs missed jobs after wake, or schedule it on a server.