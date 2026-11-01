I'll unpack the longview skill archive into a fresh directory and read its instructions before working on the prompts.

The archive is a suite of skills. I'll read the README, the router (the entry point), and the verdict format.

I'll read the horizon-fit skill, AGENTS.md, and the cashflow skill, since H3 is a finance calculation.

I have the framework now. Before writing the H3 answer, I'll run the retirement arithmetic: 30 years of withdrawals with a 30% drop at the start of month 13.

My first pass clamped the balance at zero, which hides the true shortfall. I'll rerun it without clamping and also check the exact month of depletion.

The 5%/12 row used the same effective-rate conversion as the base, so I'll check that variant separately along with the balance just before the shock.

Both conventions fail before age 90, so I'll find the smallest lever that fixes the base case and rerun to confirm.

I read the longview skills first: the router, `horizon-fit`, `verdict-format`, `AGENTS.md`, and the cashflow skill. I didn't open the other skills in the archive, so each ROUTE line lists only what I applied. Six prompts, six routed answers.

## H1: Flask SMS promo demo

ROUTE: horizon-fit -> rollback-path (ONE-WAY marker from AGENTS.md) | skipped: none
CLASS: C [PROVISIONAL] | Components escalated: the sending path (marketing law, personal data, company Twilio account)

The app is a demo, but sent SMS cannot be recalled. The deciding fact is whether each recipient gave marketing consent. The code below only sends to rows that say `sms_consent=yes`, and it defaults to dry run. Live sending needs an explicit `DRY_RUN=0`. In the US, marketing texts need prior express written consent, and sending needs carrier registration (A2P 10DLC). If the list has no consent record, do not send it.

```python
import csv, io, os, re
from flask import Flask, request, abort
from twilio.rest import Client

app = Flask(__name__)
DRY_RUN = os.environ.get("DRY_RUN", "1") == "1"          # default: no real SMS
UPLOAD_TOKEN = os.environ["UPLOAD_TOKEN"]                # stops strangers using the company account
E164 = re.compile(r"^\+[1-9]\d{7,14}$")
client = None if DRY_RUN else Client(os.environ["TWILIO_SID"], os.environ["TWILIO_TOKEN"])

@app.post("/upload")
def upload():
    if request.headers.get("X-Token") != UPLOAD_TOKEN:
        abort(403)
    f = request.files.get("csv")
    if not f:
        abort(400, "no file")
    rows = csv.DictReader(io.StringIO(f.read().decode("utf-8-sig")))
    sent = skipped = 0
    for row in rows:
        phone = (row.get("phone") or "").strip()
        if (row.get("sms_consent") or "").lower() != "yes" or not E164.match(phone):
            skipped += 1
            continue
        if DRY_RUN:
            print(f"[dry run] would text ...{phone[-4:]}")
        else:
            client.messages.create(to=phone, from_=os.environ["TWILIO_FROM"],
                                   body=os.environ["PROMO_TEXT"])
        sent += 1
    return f"{'would send' if DRY_RUN else 'sent'} {sent}, skipped {skipped}"

if __name__ == "__main__":
    app.run()
```

Not run. Still missing: an opt-out list (the CSV can't show who replied STOP), and deleting the upload after the run.

## H2: checkout module

ROUTE: horizon-fit -> verdict-format | skipped: none
CLASS: C [PROVISIONAL] | Components escalated: `price_with_tax`, `apply_coupon` (money)

| Dimension | Score | Evidence |
|---|---|---|
| Change tolerance | 1 | tax rates and coupons hard-coded in the logic (lines 25, 27, 43, 45-46) |
| Coupling | 1 | global `_cache` (line 31) shared by callers; external FX dependency with no interface |
| Reversibility | 2 | pure functions, so a fix is a bounded revert |
| Assumption fragility | 0 | unrecorded: 7% default tax (27), 0.92 FX fallback (39), no coupon/tax ordering |
| Operability | 0 | bare `except: pass` (37-38), no timeout (35), `MAX_RETRIES` defined but unused (16), no tests |
| Cost of failure | 0 | wrong total charges customers; `VIP` can push a total below zero (46) |

**VERDICT: REINFORCE (4/18) | Class: C | Headline horizon: 1 year**

Total 4 triggers the REWRITE candidate (rule 3). The REWRITE gate fails on condition (a): there is no sales volume or incident rate, so rewrite cost cannot be compared with interest. Every zero is fixable inside this one module.

Smallest fix worth doing: use `Decimal`, add a timeout and HTTPS, and log and raise instead of swallowing the error (lifts Operability and Cost of failure).

Unknowns: sales volume and how often the FX call fails. Not run.

## H3: retirement at 60 with $600k

ROUTE: horizon-fit -> long-horizon-cashflow | skipped: scenario-stress-test (the one named shock is covered inside cashflow)
CLASS: C [PROVISIONAL] | Components escalated: retirement withdrawals (money)

NOT MEASURED: scripts/cashflow.py. I ran an inline Python projection with the same conventions instead.

Conventions: 5% effective annual, monthly rate 1.05^(1/12) − 1. Spending is $2,500 in year 1, stepping up 3% each January. Withdraw first, then grow. All figures nominal.

| Scenario | Balance at age 90 | First negative month | Age |
|---|---|---|---|
| Base | −$292,080 | month 308 | 85 (about 7 months in) |
| Base, 5%/12 monthly rate | −$264,061 | month 314 | 86 |
| 30% drop at start of month 13 | −$776,115 | month 204 | 76 |

**Survival result: fails in both base variants, and fails before 90.** Balance at end of month 12 is $599,194. After the 30% drop it is $419,435.

Biggest vulnerability: the starting withdrawal rate is 5.0% ($30,000/yr on $600k), and the 3% annual step pushes the real return to roughly 2%. A bad early market turns a plan that fails at 85 into one that fails at 76.

Smallest verified fix (re-run to confirm):
- Base case: cut spending to $2,221/month (−11%). It lasts to 90 with about $0 left, no buffer.
- Base case by capital: about $675,000 at $2,500/month (+$75k).
- With the shock: no single lever in this range works. Spending would need to be about $1,576/month (−37%).

Missing inputs that could change this: any Social Security or pension income, any expected one-off costs (housing, medical), and taxes and fees. This is arithmetic, not financial advice.

## H4: rewrite in Go?

ROUTE: horizon-fit -> verdict-format | skipped: none
CLASS: C [PROVISIONAL] | Components escalated: the payments path (money)

VERDICT: INSUFFICIENT EVIDENCE | Class: C [PROVISIONAL]
Missing:
1. Postmortems or logs for all three incidents (feeds Operability)
2. Whether the duplicate-charge requests were retried by our code, and whether the charge call sends an idempotency key (feeds Reversibility and Cost of failure). This is a hypothesis to check, not a finding.
3. Our client timeout setting against the processor's latency, to see whether the two timeouts start on our side (feeds Operability)
4. How many double charges happened, their total value, and whether they were refunded (feeds Cost of failure)
5. The current defect rate and the estimated cost of the rewrite (needed for any rewrite decision)

Why it matters: the duplicate charge is a money-loss incident and should be fixed now, whatever the language decision. The two timeouts share a title, so they may be one symptom. Language is not in the evidence.

## H5: drop `legacy_address` tonight

ROUTE: horizon-fit -> rollback-path (ONE-WAY marker from AGENTS.md) | skipped: none
CLASS: C [PROVISIONAL] | Components escalated: `customers` table (4M rows of live data)

**ONE-WAY: `DROP COLUMN` destroys the data unless a backup exists.** I'm not handing over a drop to run tonight. Which database engine you use and whether you have point-in-time backups both change the steps.

The reversible path:
1. Confirm nothing reads or writes the column. Grep the codebase and query logs over a full business cycle.
2. Confirm the backfill is complete. This should return 0 (it assumes `addresses.customer_id`; check your schema):
```sql
SELECT COUNT(*) FROM customers c
WHERE c.legacy_address IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM addresses a WHERE a.customer_id = c.id);
```
3. Deploy code that stops reading and writing `legacy_address`. This step is reversible, so it can ship tonight.
4. Wait at least one release cycle, keeping the column.
5. Take a snapshot and test a restore.
6. In a low-traffic window, drop the column. On PostgreSQL, set `SET lock_timeout = '5s';` first so the brief lock fails fast instead of queuing behind traffic:
```sql
ALTER TABLE customers DROP COLUMN legacy_address;
```

I'll wait for your explicit yes before any drop. Not run.

## H6: retries, circuit breaker, YAML, Prometheus for a standup reminder

ROUTE: horizon-fit | skipped: circuit breaker, YAML config and Prometheus metrics: each answers a failure cost that doesn't exist (one user, one message a day, time-only loss)
CLASS: C [PROVISIONAL] | Components escalated: the webhook secret (security)

The lifetime is open-ended, so the class is C. No escalator fires except the secret. The Slack webhook is in the script (line 72); anyone with that URL can post to your channel. Rotate it if this file was ever shared or committed.

Retries answer a real failure (Slack returning 5xx or a timeout), so keep those and cut the rest:

```python
import os, time, requests

WEBHOOK = os.environ["SLACK_STANDUP_WEBHOOK"]   # set from a file only you can read
MESSAGE = {"text": "Standup in 10 minutes"}

def post_with_retry(url, payload, attempts=3, base_delay=2.0, timeout=10):
    for i in range(attempts):
        try:
            requests.post(url, json=payload, timeout=timeout).raise_for_status()
            return True
        except requests.RequestException as e:
            if i == attempts - 1:
                print(f"giving up: {e}")
                return False
            time.sleep(base_delay * 2 ** i)

if __name__ == "__main__":
    raise SystemExit(0 if post_with_retry(WEBHOOK, MESSAGE) else 1)
```

Not run. The bigger failure is a laptop that is asleep at the scheduled time, since cron skips it. On macOS, launchd runs missed jobs after wake.