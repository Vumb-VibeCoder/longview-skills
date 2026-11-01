---
name: codebase-longevity-audit
description: Audit a whole codebase to decide whether to keep patching, reinforce, or rewrite, using measured hotspots, line-risk scans, structure, change injection, dependencies and a debt ledger, ending in a scored verdict. Use when taking over a project, assessing repo health, or before approving a rewrite. Ships a git hotspot ranker and the line-risk scanner.
metadata:
  domain: coding
  status: READY
---
# Codebase Longevity Audit: will this codebase last?

Orchestrates the other coding skills at repo scale and ends with a verdict backed by numbers.

## When to activate
Taking over or assessing a codebase; before choosing between "keep going", "reinforce" and "rewrite". Run `horizon-fit` first; class A/B with no escalator: stop (TEMPORARY IS ENOUGH).

## Required inputs
Directory tree, dependency manifests, tests (if any), git history (if any). State what is missing, and mark the dimensions it affects as NO EVIDENCE.

## Scope rule for large repos
Above roughly 200 source files, do not claim a full audit. Audit the **top 5 hotspots** and the **2 most central modules** in depth, say the verdict applies to that sample, and list what was not examined.

## Procedure
1. **Map:** modules, dependency directions, cycles. Use `module-boundary-review` if available; otherwise read imports and state the map is manual.
2. **Hotspots (needs git):** `python scripts/hotspots.py <repo> --src <src_dir>`. Score = percentile(churn) x percentile(size), plus the count of fix commits. High churn + large + many fixes = expensive, changing and fragile: examine these first.
3. **Line risks:** `python scripts/scan_line_risks.py <repo>` for Python (candidates only; confirm by reading, as in `line-durability`). Other languages: read the hotspots manually.
4. **Boundaries:** one responsibility per module? Clear interfaces? (`module-boundary-review`)
5. **Change tolerance:** run `change-injection` with 3 scenarios drawn from `change-vectors`. If the code cannot be run or branched, label the result a desk estimate.
6. **Dependencies:** `dependency-risk`.
7. **Logic:** `logic-myopia-audit` when bugs repeat or fixes pile on fixes.
8. **Operability:** tests (do they cover the hotspots?), logging, how failures are detected.
9. **Debt:** record findings in `debt-ledger` and compute the PAY NOW set and totals.
10. **Score** with `verdict-format` (evidence from steps 1-9), present with `three-horizon-map`.
11. **Keep / reinforce / rewrite decision** (guards against the rewrite trap):
    - Prefer **REINFORCE** (incremental, hotspot by hotspot) when the debt is concentrated and there is a working system.
    - **REWRITE** is acceptable only if ALL hold: (a) the rewrite cost is less than total net interest x horizon, with ranges shown; (b) behaviour can be preserved: characterization tests or a precise specification exist or can be written first; (c) a migration path exists that does not freeze feature work for the whole rewrite (for example, replace one module at a time).
    - If (b) or (c) fails, say that a rewrite is not advisable yet and name what must exist first.

## Codebase-level myopia patterns
A god file that does everything; folder structure that does not reflect the domain; one concept named three ways; features bolted on with no shared design; tests that only cover the happy path.

## Output
```
VERDICT (verdict-format) + horizon line
Hotspots (top 5): file | churn | lines | fix commits | finding
Debt: PAY NOW set (hours, interest removed) | total principal | total net interest/month
Plan in order: smallest change that lifts the lowest score first
Not examined / NO EVIDENCE: ...
```

## Exit path
- **Missing input:** no repo or no git history: skip hotspots, mark `NOT MEASURED: hotspots`, and audit only what was provided.
- **Script problem:** if `hotspots.py`, `scan_line_risks.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** if the REWRITE gate in `verdict-format` fails, the verdict is REINFORCE, not REWRITE.

## Limits
Cannot replace domain understanding: ask the owners about things that look odd but may be intentional (consider `archaeology-test` for clarity). Git-based measures need history; squashed or shallow histories weaken them.
