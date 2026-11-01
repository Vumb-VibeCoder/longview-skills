---
name: logic-myopia-audit
description: Audit the mental model behind code that works but feels fragile: implicit invariants, special-case pile-ups, merged or wrongly split concepts, and recurring bug-fix cycles, tested against edge cases and git history. Use after a codebase audit, when fixes keep piling on fixes, or when the domain experts and the code describe the system differently.
metadata:
  domain: coding
  status: READY
---
# Logic Myopia Audit: does the model of the world hold?

Different from line review: this asks whether the **model** the code encodes can survive change in the real world.

## When to activate
After `codebase-longevity-audit`, or when code "works but feels fragile", or bugs keep recurring. Class C/D only (`horizon-fit`).

## Procedure
1. **Extract the model** in plain words: which entities exist, which relationships are fixed, which processes are the only ones. Cite the code (`file:line`) behind each statement.
2. **List the implicit invariants** ("a user has one address", "an order has one status", "a payment is in one currency").
3. **Challenge each invariant:** does the real world violate it, sooner or later? Test with **three boundary cases** (empty, many, and an unusual-but-legal case such as two addresses, a refund after a refund, a leap-day timestamp). If you cannot judge the real world, **ask a domain person**; do not guess.
4. **Look for patched special cases (M02):** many special-case `if`s mean the model is wrong, not that the cases are rare. Measure the trend from history: fix-like commits per month in the module, e.g. `git log -i --grep='fix\|workaround\|hotfix' --pretty=%ad --date=format:%Y-%m -- <path> | sort | uniq -c`. Rising is a finding; flat or falling is not.
5. **Look for merged concepts:** two different things sharing one variable, table or status only because they look alike today.
6. **Look for split concepts:** one thing divided in two only because of code history.
7. **Check vocabulary:** do the people in the domain use the same concepts as the code? A mismatch predicts future misunderstandings.
8. **Route the findings:** record the invariants in `assumption-ledger`; invariants that are risky get a tripwire (`assumption-tripwires`). Run `council-protocol` before proposing a model change, and record accepted changes with `adr-writer`.

## Mandatory questions
- If the business changes in its most plausible direction, where does this model break first?
- Is the number of special cases growing or flat? (history, not impression)
- Would a domain expert recognise this model?

## Decision per finding
| Finding | Evidence | Likelihood of violation | Decision |
|---|---|---|---|
| invariant / special-case pile-up / concept merge or split | file:line, history numbers | LOW / MEDIUM / HIGH | KEEP, RECORD TRIPWIRE, or CHANGE MODEL (via council) |

Use CHANGE MODEL only when violation is MEDIUM or higher and the cost of the model being wrong is data, money or repeated rework. Otherwise record a tripwire and move on (over-modelling is M10).

## Output
The model summary, the invariant table above, the history measurements, and open questions for domain owners.

## Limits
Requires understanding the domain. Where the AI is unsure about the real world, it must ask a person, not assume.
