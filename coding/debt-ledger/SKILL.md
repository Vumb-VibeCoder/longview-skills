---
name: debt-ledger
description: Record technical debt as principal, interest and breakeven, then decide pay-or-accept with a calculator that supports margins, residual interest and whole ledgers. Use when choosing a shortcut, prioritising refactors, auditing accumulated debt, or after horizon-fit returns TEMPORARY IS ENOUGH. Ships a calculator and an example ledger.
metadata:
  domain: coding
  status: READY
---
# Debt Ledger: debt with interest

Borrowed from finance: debt has a **principal**, an **interest** and a **breakeven**. Deliberate debt is normal; unrecorded debt is the problem.

## When to activate
Whenever a shortcut is taken, when `horizon-fit` returns TEMPORARY IS ENOUGH (this skill is then the only required follow-up), and when auditing a codebase (`codebase-longevity-audit`).

## Entry fields
| Field | Meaning |
|---|---|
| id, what | identifier and one-line description |
| basis | **how the numbers were estimated** (past incidents, measured time); an estimate without basis is not accepted |
| principal_hours | hours to fix NOW, including tests, migration, review |
| interest_hours_per_month | extra hours per month the debt costs if left (slower work, bugs, re-explaining) |
| residual_hours_per_month | optional: interest remaining AFTER the fix (default 0) |
| horizon_months | optional: months the affected code will live (from `horizon-fit`) |
| owner, due, why_taken | accountable person, re-evaluation date, why it was accepted |

## Procedure
1. **Record the debt when the shortcut is taken**, not later. Write the re-class trigger from `horizon-fit` into `why_taken` for class B items.
2. **Estimate principal and interest in hours, citing the basis.** Include the usually forgotten parts of principal (tests, data migration, coordination). Interest counts only work caused by the debt being touched or tripped over.
3. **Compute:** single debt `python scripts/debt_calc.py --principal 8 --interest 1.5 --horizon 12`; whole ledger `python scripts/debt_calc.py --ledger debt.json`. Rules used:
   - net interest = interest - residual; breakeven = principal / net interest
   - saved = net interest x horizon
   - **PAY NOW** if saved >= 1.5 x principal (the margin covers optimistic fix estimates); **MARGINAL** if principal <= saved < 1.5 x principal (accept, re-check at `due`); **ACCEPT** if saved < principal or net interest <= 0
   - no horizon given: the tool prints only the breakeven; get the horizon from `horizon-fit` first
4. **Rank for payment** by relative rate (net interest / principal), highest first: high interest, low principal goes first.
5. **Check interactions by hand:** does this debt raise the interest of another? If so raise that entry's interest and say why.
6. **Review on `due`:** the script flags OVERDUE entries; re-estimate with fresh evidence, then pay, accept again with a new date, or delete if the code is gone.

## Mandatory questions
- If nobody touches this code again, is the interest really zero? (Untouched debt accrues no interest: accepting it is right.)
- Does paying it remove the interest, or only part of it (residual)?
- Is the principal missing tests or migrations?

## Failure patterns
No interest estimate; principal underestimated; no owner or due date (debt becomes permanent); using the ledger to justify everything as "accept".

## Output
The ledger (JSON in the template format), the calculator output, and the PAY NOW set with its total principal and interest removed.

## Limits
Hour estimates are rough: use them to rank and choose, not to report precisely. The same frame works for non-code debts (see the `finance` skills when available).
