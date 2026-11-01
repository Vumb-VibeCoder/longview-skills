---
name: three-horizon-map
description: Judge a decision or verdict at three horizons (now, 1 year, 5 years), identify the tipping point where a good choice turns bad, and decide whether to pay now or defer. Use when a choice that is fine today may become a burden later, and for class C/D verdicts before verdict-format.
metadata:
  domain: core
  status: READY
---
# Three Horizon Map: now / 1 year / 5 years

A solution that is right at one horizon can be wrong at another. See all three, then act only where acting is cheaper than waiting.

## When to activate
Class C/D decisions and verdicts. Class A/B with no escalator: skip. Run after `council-protocol` and before `verdict-format`.

## Procedure
1. For the decision, fill one row per horizon:

   | Horizon | Verdict (KEEP / REINFORCE / REWRITE) | What would break it | Evidence or scenario | Action |
   |---|---|---|---|---|
   | Now | | | | |
   | 1 year | | | | |
   | 5 years | | | | |

   Use the verdict names from `verdict-format`.
2. **Label confidence:** now = measured; 1 year = projected from trends or the change vectors; 5 years = **SCENARIO** (not a forecast). Say what each rests on.
3. **Tipping point:** if a verdict worsens from one horizon to the next, state **when** and **what observable sign** will show it is happening (this becomes a tripwire).
4. **Pay now or defer?**
   - A later-horizon problem that is cheap to fix when it arrives: **accept** (do not pre-pay), provided the fix is not blocked by a one-way door such as stored data format, a public API or a contract (`reversibility-check`).
   - A later-horizon problem that is blocked by a one-way door: **pay now**, or add the cheapest reversible hedge.
   - Bad now but fine later: fix now only if the pain is real today.
   - **Bad at all three horizons:** this is a design flaw, not a timing issue; do not hide it behind horizons.
5. Hand the horizon line to `verdict-format`. The headline verdict follows the class: C = the 1-year column, D = the 5-year column. A 5-year SCENARIO alone does not justify action unless step 4 says it is blocked by a one-way door.

## Output
The table above, the tipping points with their observable signs, and the line `now <V> | 1 year <V> | 5 years <V>`.

## Limits
The 5-year column is scenario thinking. State the confidence and the main scenario it depends on.
