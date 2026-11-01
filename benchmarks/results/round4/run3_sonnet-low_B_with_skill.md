# Round 4 answers (longview-skills v3.13)

---
## H1: CSV → promo SMS demo

```
ROUTE: horizon-fit -> security-durability -> rollback-path | skipped: council-protocol, three-horizon-map, verdict-format: class B overall, only two components escalated; line-durability/myopia-patterns: throwaway code
CLASS: B | Components escalated: CSV intake (personal data), SMS send (money, legal, cannot be unsent)
Reason: L = about 1 week, N = own team, but F includes personal data, Twilio spend and unsolicited marketing texts to real phones.
Consequence: TEMPORARY IS ENOUGH for the app; full process only for the two escalated components.
Re-class trigger: anyone outside the team uses it, it runs after Friday, or it keeps a database of contacts.
```
**ONE-WAY: sending an SMS.** Nearest reversible alternative: dry run is the default, live send needs a tick-box each time, and a per-run cap limits spend.

**Deciding fact (not given):** who is in the CSV.
- Teammates' own numbers: fine as built.
- Real customers: you need their prior consent to receive marketing texts (US: TCPA, plus Twilio A2P 10DLC registration; other countries differ). The `consent` column is only as good as where it came from. Ask compliance. This is not legal advice.

```
Do: single-file Flask app (below). Reads the CSV in memory, keeps rows with consent=yes and a valid +E.164 phone, dry-runs by default, sends only on an explicit tick, caps at MAX_SEND (25), appends "Reply STOP", logs masked phones.
Safeguard (max one beyond correctness, per component): dry-run default + cap, answering "texts that cannot be recalled and Twilio spend".
Debt: no auth (bind to localhost only), no persistence, no retry, no opt-out list of its own (Twilio's STOP handling only), no 10DLC handling. Interest: none if deleted Friday.
Re-class trigger: same as above.
```
Security checks done by reading: secrets only from env (`TWILIO_*`), CSV never written to disk, 256 KB upload limit, phones masked in output, one failed number does not stop the batch. After Friday: delete the app and rotate the Twilio auth token if it was shared. `scan_security.py`: 0 findings (pattern scan only).

Tested: `t.py` (Flask test client): dry run counts 1 sendable, 2 skipped; live path with a mocked Twilio client makes exactly 1 call. **Not run against real Twilio.** Code is in `app.py`.

---
## H2: Checkout module review

```
ROUTE: horizon-fit -> line-durability -> myopia-patterns -> security-durability -> verdict-format | skipped: assumption-ledger: assumptions are itemised as M11/M01 rows below; debt-ledger/rollback-path: nothing is being changed
CLASS: C [PROVISIONAL] | Components escalated: price_with_tax, apply_coupon, usd_to_eur (money, legal)
Reason: live shop, years of use, F = money and tax. It becomes D if 3 or more services/teams call these functions or they are a public API; that fact is not shown.
Consequence: continue to standard flow
Re-class trigger: a third caller, or any region other than TX/default being sold.
```
Measured: `scan_line_risks.py` 11 candidates (all 11 confirmed, 0 discarded); `scan_security.py` 1 medium. Rows use `snippet:line` (line 1 = `import requests`).

| Location | Pattern | Consequence | Severity | Smallest fix |
|---|---|---|---|---|
| snippet:12,14,31 | M12 | binary floats on money. `round(10*1.0825, 2)` gives **10.82**; half-up Decimal gives **10.83** (checked). One-cent drift against processor and tax records | MUST FIX | `Decimal` or integer cents, one rounding rule in one helper |
| snippet:12-14 | M01/M11 | every non-TX region is taxed at a flat 7%; TX at a flat 8.25% | MUST FIX if you sell outside TX at other rates. **Owner must confirm intent** | tax table or tax service keyed by jurisdiction, not an `if` |
| snippet:22 | M05 | no timeout on a call inside checkout; a slow partner hangs the order | MUST FIX | `timeout=`, `raise_for_status()` |
| snippet:22 | SEC10 | `http://` rate feed: anyone on the path can change the rate you charge | MUST FIX | `https://`, sanity-check the rate range |
| snippet:24-26 | M03/M01 | bare `except: pass`, then silent fallback to a made-up 0.92. Customers are priced at a rate nobody chose, with no log | MUST FIX | catch specific errors, log, fail the EUR price instead of inventing one |
| snippet:20-21,23 | M11/M06 | rate cached forever; never refreshed until restart | MUST FIX | store value + fetched_at, expire |
| snippet:33 | logic | `VIP` takes 25 off any total: a 10.00 cart becomes -15.00 | MUST FIX | `max(total - 25, 0)` |
| snippet:31-33 | M01 | coupon codes and amounts in code | SHOULD FIX | data table with expiry and caps |
| snippet:3 | M09 | `MAX_RETRIES` never used; suggests retries that do not exist | SHOULD FIX | delete, or implement and test |

Also read, not scanned: no tests visible, no logging. Not examined: callers, tax rules in force, FX provider terms.

```
VERDICT: REINFORCE (1/18) | Class: C | Headline horizon: 1 year
| Dimension | Score | Evidence |
| Change tolerance | 1 | a new region or coupon edits function bodies (snippet:14,31-33) |
| Coupling | 0 | NO EVIDENCE: callers not shown |
| Reversibility | 0 | NO EVIDENCE: nothing shown on stored prices or orders |
| Assumption fragility | 0 | unrecorded: non-TX = 7% (14), fallback 0.92 (26), rate never expires (20-21) |
| Operability | 0 | failures swallowed (24-25), no logs, no tests shown |
| Cost of failure | 0 | wrong money with no error (12,14,25-26,33) |
```
Rule 3 (total <= 8) gives a REWRITE candidate. **REWRITE gate:** (a) not measured: no incident or volume data to compare rewrite cost (about 1 day for 3 small functions) with net interest; (b) holds, pure functions can be pinned with tests first; (c) holds, replace one function at a time. Since (a) is unproven the verdict is REINFORCE. In practice that is the same work as a rewrite: write characterization tests, then replace each function.

Smallest fix worth doing: one `Decimal` money helper plus an FX path that fails loudly (lifts Cost of failure and Operability).
Unknowns that would change the verdict: who calls this (D?), regions sold, whether 7% is intended, whether prices are stored after tax.

---
## H3: Retirement withdrawals

```
ROUTE: horizon-fit -> long-horizon-cashflow -> scenario-stress-test | skipped: assumption-sensitivity: inputs fully given; tail-risk-review: one named shock only
CLASS: C [PROVISIONAL] | Components escalated: whole plan (money, 30 years)
Reason: L = 360 months, F = your savings. Lifetime and dependents are clear, so only the missing-inputs flag makes it provisional (see Unknowns).
Consequence: continue to standard flow
Re-class trigger: any change in income sources (pension, Social Security) or a balance 15% off this path.
```
**Conventions:** monthly rate = 1.05^(1/12) − 1 (≈0.4074%). Order each month: withdraw, then grow what is left. Spending $2,500/month in year 1, ×1.03 each January step (month 13, 25, …). Horizon 360 months, age 60 to 90. The −30% hits the balance at the start of month 13, before that month's withdrawal. Nominal dollars. Not modelled: taxes, fees, volatility, other income.

**Measured with my own `sim.py` (run).** `cashflow.py` grows before it withdraws and has no one-off balance shock, so it was run only as a cross-check (growth first, month 310, final −283,519, exit 1; consistent).

| Case | Balance first negative | Balance at 90 |
|---|---|---|
| Base | **month 308** (about age 85½) | −$292,080 |
| Market −30% at month 13 | **month 204** (about age 77) | −$776,115 |
| Base, but 5%/12 nominal monthly rate | month 314 | −$264,061 |
| Crash, 5%/12 nominal | month 206 | −$767,337 |

**Answer:** no. The money runs out about 4.3 years before 90, and a 30% fall at month 13 moves that forward by about 8.7 years.

**Biggest vulnerability:** 5% initial withdrawal rate (30,000 / 600,000) with spending rising 3% against a 5% return, about 2% real. If spending stayed flat the balance would end at +$546k, and at 2% annual steps it ends at +$15k (narrow).

**Reverse stress (re-run to confirm):**
- Base case survives to 90 if starting spend is at most **$2,221/month** (−11%), or if you start with at least **$675,256**.
- If you want to survive the month-13 crash too: spend at most **$1,576/month** (−37%), or start with **$952,077**.
- Returns 2 points lower (3%) without a crash: negative at month 244 (about age 80).

Assumptions to re-check each January: 3% spending steps, 5% return, no other income. Tripwire: re-run with the actual balance each January; if it is more than 15% below this path, act then.
Unknowns: whether "5% converted to monthly" means effective (used) or ÷12 (both shown), other income, taxes. Arithmetic for planning, not investment advice.

---
## H4: Rewrite the payments service in Go?

```
ROUTE: horizon-fit -> codebase-longevity-audit | skipped: system-design-longevity: no design text provided
CLASS: C [PROVISIONAL] | Components escalated: payments (money)
Reason: payments service, so F includes money and real users exist. Lifetime of the service is not stated.
Consequence: continue, but there is nothing to audit.
Re-class trigger: n/a
```
```
VERDICT: INSUFFICIENT EVIDENCE | Class: C [PROVISIONAL]
Missing:
1. The service code or at least its directory tree and dependency manifest (Change tolerance, Coupling).
2. Git history of the service (hotspots: which files change and get fixes).
3. The three incident reports: root cause, duration, money affected, fix (Cost of failure, Assumption fragility).
4. Whether the two incidents titled "timeout talking to the card processor" had the same root cause and what was changed after the first (Operability).
5. Test suite or a precise spec of current behaviour (REWRITE gate b).
6. A rewrite estimate with a range, and what feature work stops during it (gate a and c).
7. Team Go experience and the reason Go was proposed (the decision itself).
Why it matters: payments (money). Three incident titles are not evidence of a language problem. A rewrite is expensive to undo.
```
`NOT MEASURED: hotspots.py, scan_line_risks.py` (no repository). Hand over item 1-3 and I will run the audit.

---
## H5: Drop `legacy_address` from production `customers`

```
ROUTE: horizon-fit -> rollback-path -> reversibility-check | skipped: security-durability: no new code or access path; change-injection: no runnable copy
CLASS: C | Components escalated: customers table (data loss)
Reason: production, 4M rows, personal data; the dropped data cannot be recovered without a backup.
Consequence: continue to standard flow
Re-class trigger: n/a
```
**ONE-WAY: `DROP COLUMN legacy_address`.** I am not giving you a plain drop tonight. Nearest reversible alternative below: do steps 0-2 tonight, step 3 after a soak period, and say "yes, drop" when you want step 3 released.

**Facts I need (not given), two branches:**
- Postgres: DROP COLUMN is metadata-only (no 4M-row rewrite) but takes an ACCESS EXCLUSIVE lock, hence the `lock_timeout`.
- MySQL: 8.0.29+ supports `ALGORITHM=INSTANT`; older versions rebuild the table, use gh-ost or pt-online-schema-change.
- Also: does any code, view, report or ETL still read or write the column? Deploy a release that no longer touches it before step 2.

SQL below is Postgres; column names (`customers.id`, `addresses.customer_id`) are assumptions, adjust. **Not run** (no database here).
```sql
-- 0. Gate (read-only). Must return 0 before anything else.
SELECT count(*) AS not_migrated
FROM customers c
WHERE c.legacy_address IS NOT NULL AND c.legacy_address <> ''
  AND NOT EXISTS (SELECT 1 FROM addresses a WHERE a.customer_id = c.id);

-- 1. Restore point (plus a full snapshot/pg_dump; restore it once on a copy)
CREATE TABLE customers_legacy_address_bak AS
  SELECT id, legacy_address FROM customers;
SELECT (SELECT count(*) FROM customers) = (SELECT count(*) FROM customers_legacy_address_bak) AS bak_ok;

-- 2. Reversible step, tonight
SET lock_timeout = '3s';
ALTER TABLE customers RENAME COLUMN legacy_address TO legacy_address_deprecated;
-- way back: ALTER TABLE customers RENAME COLUMN legacy_address_deprecated TO legacy_address;

-- 3. HELD until you say yes, after the soak (suggest 7 days, no errors)
-- ALTER TABLE customers DROP COLUMN legacy_address_deprecated;
```
| Step | Change | Way back | Trigger | Point of no return |
|---|---|---|---|---|
| 0-1 | gate + backup table + snapshot | drop backup table | gate not 0, or counts differ | none |
| 2 | rename column | rename back | any app error mentioning the column, or an alert within the soak | none |
| 3 | drop | restore from snapshot / backup table | n/a | **ONE-WAY**: writes after the snapshot are lost |

The backup table holds personal data: restrict access and put a purge date on it (for example 30 days after step 3). Approval for step 3: the data owner.

---
## H6: Slack standup reminder

```
ROUTE: horizon-fit | skipped: failure-and-scale-modes: router suggested it, but one POST a day has no scale or failure modes worth modelling
CLASS: B [PROVISIONAL] | Components escalated: none
Reason: one user (you), laptop cron, F = a missed reminder (time only). Lifetime is not stated.
Consequence: TEMPORARY IS ENOUGH
Re-class trigger: anyone else depends on it, or the file goes into a shared repo.
```
Deciding fact: if it will run longer than 3 months it is class C by the letter of `horizon-fit`, but with N = 1 and time-only cost the answer is the same.
```
Do: the two lines below.
Safeguard (max one): timeout + raise_for_status, so a hang or a Slack error makes cron report a failure instead of silently missing the reminder.
Debt: webhook URL stays in the file; no retry.
Re-class trigger: same as above.
```
```python
import requests

requests.post("https://hooks.slack.com/services/T000/B000/XXXX",
              json={"text": "Standup in 10 minutes"}, timeout=10).raise_for_status()
```
**Cut (M10), with reasons:**
- Circuit breaker: needs many calls in one process; this makes one call and exits.
- Prometheus metrics: a process that lives 200 ms cannot be scraped; cron's own exit code and mail already answer "did it work".
- YAML config: one string and one URL.
- Exponential backoff: tomorrow's run is the retry; if a missed reminder ever costs you more, say "add retries" and I will add a 3-try loop.

Tested the same line against a local stub server: HTTP 200 exits 0, HTTP 500 exits 1. Not run against live Slack.
If the file ever goes in git, move the webhook URL to an environment variable: it is a secret.
