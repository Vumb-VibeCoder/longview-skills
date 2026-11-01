---
name: assumption-tripwires
description: Attach an automated check, a warning threshold, an expiry date and an owner to each risky assumption so it raises an alarm when it stops being true. Use after assumption-ledger, when setting up CI monitoring of assumptions, or when asked how we would know an assumption broke. Ships a ledger checker script (expiry, missing tripwires, live checks) and an example ledger.
metadata:
  domain: core
  status: READY
---
# Assumption Tripwires: assumptions that raise their own alarm

Writing an assumption down is not enough. A risky assumption must **announce when it stops being true**, early enough to act.

## When to activate
After `assumption-ledger` has entries that require a tripwire (impact=HIGH and not VERIFIED, or impact=MEDIUM and GUESSED). Class A/B with no escalator: skip.

## Tripwire fields
| Field | Meaning |
|---|---|
| check | what is measured, in words |
| check_command | the executable check; **exit 0 = assumption still holds, non-zero = tripped** |
| threshold | the alarm level, set at about 50% of the true failure point (or earlier if the fix takes long) |
| on_trigger | the concrete action when it trips |
| expires, owner | re-verification date; a named person or team |

## Procedure
1. Take the entries needing a tripwire from the ledger.
2. **Pick the check type** (prefer automatic, runnable in CI or on a schedule):
   | Assumption kind | Check |
   |---|---|
   | data size/volume | assertion or metric with threshold, logged each run |
   | external API shape | contract test against a recorded schema |
   | library/runtime version | pinned version plus a check on the installed version |
   | maintenance of a dependency | script checking last release date against a limit |
   | law/regulation/price | dated review task; also add a `check_command` that fails when the date passes |
   | people/knowledge | bus-factor check (e.g. commits by author) or handover test |
3. **Set the threshold with lead time:** `threshold = failure point - (time to fix x growth rate)`. If you cannot estimate growth, use 50% of the failure point and say so.
4. **Write `check_command` as a real command.** A placeholder that always exits 0 is false assurance and is forbidden. If an automated check is impossible, record why, and use an expiry-driven review (and note the entry is MANUAL).
5. **Validate:** `python scripts/tripwire_check.py ledger.json` (add `--run` to execute checks). It reports INVALID, EXPIRED, EXPIRING, UNMONITORED, TRIPPED and CHECK-ERROR; exit code 1 on any finding, so it can gate CI or a weekly job.
6. **Prove the tripwire can fire:** temporarily force the condition (or lower the threshold) and confirm the command exits non-zero. An untested tripwire is untrusted.
7. Treat TRIPPED or EXPIRED as work items: execute `on_trigger`, or re-verify and set a new expiry with fresh evidence.

## Mandatory questions
- If this assumption broke silently, who or what would notice, and after how long?
- Does the threshold leave enough time to fix before real failure?
- Can the check itself break silently (credentials expired, test skipped)?

## Failure patterns
- No owner: nobody acts. Threshold equal to the failure point: the alarm arrives too late. Expiry longer than 12 months for fast-moving things. A check that never ran. A tripwire that fires so often it is ignored (tune it, do not mute it).

## Output
The updated ledger JSON, the `tripwire_check.py` result, and a list of entries that are MANUAL with the reason.

## Limits
Catches only assumptions that were stated and are measurable. `--run` executes the commands in the file without a shell; run only ledgers you trust.
