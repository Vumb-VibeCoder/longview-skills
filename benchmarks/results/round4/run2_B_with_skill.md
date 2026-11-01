Before I start the six tasks, I'll apply the longview routing to each. For H3 (retirement money) the router names `long-horizon-cashflow`, so I'll read its template and script and run them.

The skill's script grows the balance before withdrawing, but you specified withdraw-first. I'll run a small model that follows your order, with the shock applied before month 13's withdrawal.

The H3 numbers are in. Next I'll write the H1 demo with consent and dry-run safeguards, and the minimal H6 script, then syntax-check both.

## H1: Promo SMS demo

ROUTE: horizon-fit | skipped: verdict-format: no review requested
CLASS: C (escalated: sending messages and storing phone numbers)

File: `/tmp/claude-0/-home-claude/a75ede3f-131a-52bd-993a-a6aa05a4896d/scratchpad/h1/app.py`

It's a throwaway, but it messages real people, and marketing SMS needs consent in most places. So the app:
- messages only rows where `consent=yes` and the phone is valid E.164
- runs in dry-run mode unless `SEND_LIVE=1` is set
- appends an opt-out line to every message
- never writes the CSV to disk

For Friday, use Twilio test credentials or your own numbers. Not run: it compiles, but Flask and Twilio were not exercised against a live account.

## H2: Checkout module

ROUTE: horizon-fit -> verdict-format | skipped: line-durability: not read in this pass; findings come from the code shown
CLASS: D [PROVISIONAL: dependent count unknown] | Components escalated: all (money)

```
VERDICT: REINFORCE (4/18) | Class: D | Headline horizon: 5 years
| Dimension | Score | Evidence |
| Change tolerance | 1 | region tax rules inline (snippet L24-27); a new region edits this function and its callers |
| Coupling | 1 | usd_to_eur mixes an external HTTP call with a module-global cache (L31-39) |
| Reversibility | 2 | 40-line module; undo is days |
| Assumption fragility | 0 | non-TX rate 7% (L27), FX fallback 0.92 (L39), coupon order and VIP floor unrecorded |
| Operability | 0 | bare except (L37-38) hides failures; no timeout on requests.get (L35); no tests |
| Cost of failure | 0 | a wrong total is charged to customers silently |
```

Total is 4, which would be a REWRITE candidate, but the rewrite gate fails on behaviour preservation: there is no spec for the 7% non-TX rule or the coupon order. So the verdict is REINFORCE.

Other findings from the snippet:
- Money is computed in floats (L23-28, 44, 46). Use Decimal or integer cents.
- L33: the FX rate is cached forever and never refreshed.
- L35: no timeout, so a hung partner server can hang checkout.
- L36: plain `http://` URL.
- L46: the VIP coupon has no floor, so a small cart can go negative.

Smallest fix: add a timeout and catch only specific exceptions in `usd_to_eur`, with logging. This lifts Operability and Cost of failure.

Unknowns: the real region tax table, the coupon order, and whether `usd_to_eur` is on the checkout path.

## H3: Retirement, $600k

ROUTE: horizon-fit -> long-horizon-cashflow -> scenario-stress-test | skipped: assumption-sensitivity: inputs not uncertain in the request
CLASS: C (money, multi-year)

| Case | Monthly rate | Money runs out | Balance at month 360 |
|---|---|---|---|
| No shock | (1.05)^(1/12)−1 | month 308 (age 85 y 7 m) | −$292,080 |
| 30% drop at month 13 | same | month 204 (age 76 y 11 m) | −$776,115 |
| No shock | 5%/12 | month 314 (age 86 y 1 m) | −$264,061 |
| 30% drop at month 13 | 5%/12 | month 206 (age 77 y 1 m) | −$767,337 |

**No, the money does not last to 90.** It runs out around age 85 without a shock, and around 77 with the drop. To last to 90 with no shock, the starting spend would be about $2,220 a month.

Assumptions: withdraw first, then grow, as you specified. The skill's bundled script grows first, so it would show slightly better results. No taxes or fees. Spend rises 3% each plan year. This is a framework for thinking about the numbers, not financial advice.

## H4: Rewrite the payments service in Go?

ROUTE: horizon-fit -> verdict-format | skipped: codebase-longevity-audit: no code provided to audit
CLASS: C (payments, money)

```
VERDICT: INSUFFICIENT EVIDENCE | Class: C [PROVISIONAL]
Missing:
1. Write-ups or root-cause findings for the 3 incidents (feeds Operability, Cost of failure)
2. Card-processor client code: timeout, retry and idempotency-key handling (feeds Change tolerance)
3. Root cause of the double charge: was a retry sent without an idempotency key? (feeds Cost of failure)
4. Service size and number of owners (feeds the horizon)
Why it matters: the double charge is a money incident, and a language change does not address it.
```

From the titles alone, two of the three incidents are the same timeout to an external processor, which Go would not change. The double charge points to retries without idempotency, not to language. Don't decide on Go yet. Check idempotency keys and timeouts first.

## H5: Drop `legacy_address` tonight

ROUTE: horizon-fit -> rollback-path | skipped: verdict-format: no review requested
CLASS: C (customer data, production) | ONE-WAY: `DROP COLUMN`

I won't write an immediate drop for tonight. Once it runs, the data is gone except from a restore. The nearest reversible option is to rename the column tonight and drop it after a grace period. I assumed PostgreSQL and that `addresses.customer_id` links the rows. Tell me if either is wrong.

Order matters: release the app version that no longer reads or writes `legacy_address` first. Renaming while old instances still read it will break them.

Take a snapshot first, then check the backfill. This must return 0:

```sql
SELECT COUNT(*) FROM customers c
WHERE c.legacy_address IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM addresses a WHERE a.customer_id = c.id);
```

Tonight (rename, reversible):

```sql
ALTER TABLE customers RENAME COLUMN legacy_address TO legacy_address_deprecated;
```

Way back: `ALTER TABLE customers RENAME COLUMN legacy_address_deprecated TO legacy_address;`

Later, after 2–4 weeks with no reads in the logs and a fresh backup: `ALTER TABLE customers DROP COLUMN legacy_address_deprecated;` This waits for your explicit yes.

Not run: no database was available.

## H6: Standup cron script

ROUTE: horizon-fit | skipped: all others: a one-user reminder has no matching skill
CLASS: B (own use, time only) → TEMPORARY IS ENOUGH

File: `/tmp/claude-0/-home-claude/a75ede3f-131a-52bd-993a-a6aa05a4896d/scratchpad/h6/standup.py`

- **Do:** read the webhook from an env var, set a 10-second timeout, and exit non-zero on failure so cron logs it.
- **Not added:** retries, circuit breaker, YAML config and Prometheus. None of them answers a failure worse than a missed reminder, and cron retries tomorrow anyway.
- **Safeguard:** timeout and non-zero exit, which prevent a silent hang.
- **Debt:** no retry, so a Slack outage costs one reminder.
- **Re-class trigger:** anyone else uses it, or it still runs after 2027-05-01. Either makes it class C.

If the webhook URL was ever committed to git, rotate it.

Not run: it compiles, but no request was sent to Slack.