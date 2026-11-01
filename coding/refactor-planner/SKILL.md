---
name: refactor-planner
description: Turn audit findings and debt entries into a safe, ordered plan of small reversible refactoring steps (characterization tests first, seams before moves, never mixing behaviour change), validated by a script for ordering, step size and missing safety nets. Use after a codebase audit, boundary review or debt-ledger decision to PAY or REINFORCE, and before approving any rewrite. Ships a plan validator and an example plan.
metadata:
  domain: coding
  status: READY
---
# Refactor Planner: change the structure safely

Converts "this should be better" into steps that can each be shipped, verified and undone. A refactor with no safety net is a rewrite in disguise.

## When to activate
After `codebase-longevity-audit`, `module-boundary-review`, or a `debt-ledger` result of PAY NOW, or a verdict of REINFORCE or REWRITE from `verdict-format`. Class C/D only (`horizon-fit`). Do not plan a refactor without a **driver**: a hotspot, a coming change (`change-vectors`), or debt with interest. "It would be cleaner" is not a driver (M10).

## Required inputs
The findings with evidence, the debt ids involved, the test situation, and the remaining lifetime of the affected code. If the lifetime is shorter than the debt's breakeven, stop: accept the debt.

## Step types
| Type | Meaning |
|---|---|
| CHARACTERIZE | write tests that pin **current** behaviour (including quirks), before any change |
| SEAM | introduce an interface/adapter at a point that already has two sides, with no behaviour change |
| MOVE | relocate code or data to the right module |
| REPLACE | swap an implementation behind a seam |
| DELETE | remove dead or replaced code |
| CLEANUP | renames and tidying with no structural effect |

## Procedure
1. **State the goal and the measurable end condition** in numbers: for example "0 import cycles between billing and orders (module_graph)", "0 M01 findings in billing.py", "radius for scenario X drops from 6 modules to 2 (blast_radius)". No measurable end condition, no plan.
2. **Establish the safety net first.** If the affected behaviour lacks trustworthy tests, the first steps are CHARACTERIZE. A test that was never seen to pass on the current code and fail on a deliberately broken version is not trusted.
3. **Break the work into steps of 16 hours or less**, each one **independently shippable**: the system works after every step. Prefer many small steps over one big one. Prefer incremental replacement of one piece at a time over a flag day.
4. **Order the steps:** CHARACTERIZE, then SEAM, then MOVE/REPLACE, then DELETE, then CLEANUP. Among independent steps do the highest relative debt rate first (net interest / principal from `debt-ledger`).
5. **Never mix a behaviour change into a refactoring step.** Behaviour changes are separate work items with their own tests. If a bug is found while refactoring, record it and fix it separately.
6. **For every step** write: the goal, dependencies, hours, `verify` (a command or measurement that proves it is done and nothing broke), `rollback` (usually `git revert`; for data or schema changes state the real undo path), and `debt_ids`.
7. **Validate:** `python scripts/plan_check.py plan.json`. It rejects cycles, unknown dependencies, steps over 16 hours, missing verify or rollback, `behavior_change: true`, and MOVE/REPLACE/DELETE steps with no CHARACTERIZE step in their chain (unless `tests_exist: true` is declared and justified).
8. **Check one-way doors:** a step that changes stored data, a public API or a contract is a ONE-WAY door: handle it with `reversibility-check` and record it with `adr-writer`.
9. **Pre-commit to stop rules:** a time-box, and a condition under which the plan is abandoned (for example, the radius metric does not improve after the SEAM step). Re-run the relevant measurement after every few steps and update the debt ledger with real hours spent: this feeds better estimates.
10. If the plan amounts to a full rewrite, apply the rewrite guard in `codebase-longevity-audit` (cost vs interest, behaviour preserved, no feature freeze).

## Mandatory questions
- After step N, can we stop and still be better off than before?
- What proves each step changed structure but not behaviour?
- Which step is the first one that is hard to undo, and have we reduced the risk before it?

## Output
The plan (JSON in the template format), the `plan_check.py` result (order, total hours, critical path), the measurable end condition, and the stop rule.

## Limits
Hour estimates are rough. The validator checks plan structure, not whether the tests are good or the steps are right. Dynamic behaviour (reflection, runtime configuration) can defeat characterization tests: say where they are weak.
