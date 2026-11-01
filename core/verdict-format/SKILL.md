---
name: verdict-format
description: Produce the standard long-term verdict with six scored dimensions, cited evidence and a decision rule (KEEP, REINFORCE, REWRITE, TEMPORARY IS ENOUGH, INSUFFICIENT EVIDENCE). Use at the end of every durability, long-term risk or architecture review so results are consistent and checkable.
metadata:
  domain: core
  status: READY
---
# Verdict Format: scored, evidenced, reproducible

Every Longview skill ends with this format. Scores exist to make judgments comparable, not to be precise.

## Preconditions
Run `horizon-fit` first. If its result is class A/B with no escalator, the verdict is **TEMPORARY IS ENOUGH** and nothing below is scored.

## Six dimensions, scored 0-3 (higher is always better)
| Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| Change tolerance | a plausible requirement change touches many places | touches several modules | touches one module plus callers | touches 1-2 places, all named |
| Coupling | editing one place breaks distant places | shared internals across modules | narrow interfaces with some leaks | independent modules, explicit interfaces |
| Reversibility | wrong decision cannot be undone | undo needs a migration or rewrite | undo needs bounded effort (days) | undo is cheap (hours, flag, revert) |
| Assumption fragility | many unrecorded implicit assumptions | assumptions known but unmonitored | key assumptions recorded | recorded AND guarded by a tripwire |
| Operability | failures are silent, no tests | partial tests or logs | tests plus logs, slow to localise | failures are detected fast and localised |
| Cost of failure | failure loses money/data/safety | recoverable but costly loss | bounded, recoverable loss | only minor time lost |

**Evidence rule:** a score needs evidence (code `file:line`, a measurement, a named assumption). A dimension with no evidence scores 0 and is marked `NO EVIDENCE`.

## Decision rule (apply in this order, first match wins)
1. Class A/B with no escalator: **TEMPORARY IS ENOUGH**.
2. Three or more dimensions are `NO EVIDENCE`: **INSUFFICIENT EVIDENCE** (list exactly what to gather; do not output REWRITE/KEEP).
3. Total <= 8, OR (Change tolerance <= 1 AND Coupling <= 1): **REWRITE**.
4. Total >= 14 AND no dimension = 0: **KEEP**.
5. At least one dimension = 0, but every zero can be fixed locally (one module, bounded effort): **REINFORCE**.
6. Total 9-13 and no dimension = 0: **REINFORCE**.
7. Otherwise (a zero that cannot be fixed locally): **REWRITE**.

Rule 3 outranks rule 4 on purpose: a system that scores 14/18 but cannot absorb change AND is tightly coupled is still a REWRITE.

## Headline horizon
The headline verdict is computed for the horizon implied by the class: C = 1 year, D = 5 years. If `three-horizon-map` was run, also print the per-horizon line.

## Output (exact shape)
```
VERDICT: REINFORCE (11/18) | Class: C | Headline horizon: 1 year
Horizons (optional): now KEEP | 1 year REINFORCE | 5 years REWRITE
| Dimension | Score | Evidence |
| Change tolerance | 1 | currency hard-coded in 6 places (billing.py:12,40,...) |
...
Smallest fix worth doing: <one concrete change, with the dimension it lifts>
Unknowns: <what would change the verdict>
```

## INSUFFICIENT EVIDENCE shape
Use when rule 2 fires, or when the thing to review was not provided at all. Print:
```
VERDICT: INSUFFICIENT EVIDENCE | Class: <class> [PROVISIONAL]
Missing: <numbered list of exact inputs, each with the dimension it feeds>
Why it matters: <one line naming the escalator, if any>
```
Do not rank speculative risks. Questions to answer are allowed; findings are not.

## Limits
The scale is a consistency tool, not truth. If two reviewers differ, compare evidence, not numbers.
