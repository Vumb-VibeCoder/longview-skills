---
name: skill-router
description: Choose which Longview skills to apply to a request, in what order, and which to skip. Run at the very start of EVERY request that involves code, a design, a financial plan, a UI, a decision or a review, before horizon-fit. Maps request types to a minimal skill set, handles missing artifacts and multi-domain requests, and fixes the mandatory ROUTE and CLASS header. Ships route.py, a keyword router with a regression test set.
metadata:
  domain: core
  status: READY
---
# Skill Router: the right skill for each request

Testing showed most failures were routing failures: money questions answered without the finance skills, ceremony for one-off tasks, reviews given with nothing to review. Run first; stay silent for pure conversation or how-it-works questions.

## Procedure
1. **Name the request type** from the table (one primary, at most one secondary).
2. **Artifact check.** If a review or verdict is requested and the thing to judge (code, design text, numbers, diagram) is missing or too thin, output `VERDICT: INSUFFICIENT EVIDENCE` (shape in `verdict-format`), list the exact inputs needed, and rank no risks.
3. **Run `horizon-fit`.** Class A/B with no escalator ends routing: TEMPORARY IS ENOUGH path only.
4. **Pick the minimal set:** at most 4 skills besides `horizon-fit` and `verdict-format`, each answering a risk named in the CLASS reason. A skill that would not change the answer goes under `skipped` with the reason.
5. **Order:** `horizon-fit`, measuring skills (those with scripts), judgment skills, `council-protocol` if torn, `three-horizon-map`, `verdict-format` (class C/D reviews only), recording skills (`debt-ledger`, `adr-writer`, `calibration-loop`).
6. **Apply what you name.** Each skill in ROUTE must leave a visible trace in the answer (table, number, pattern ID, verdict line); otherwise move it to `skipped`.
7. **Run the scripts** the chosen skills ship when a shell exists. If not, write `NOT MEASURED: <what>` and give a hand-computable bound. Never claim a run that did not happen.
8. **Multi-domain requests:** route each component separately and say which component each skill covers.
9. Helper: `python scripts/route.py "<request>"` suggests a set by keywords. The table and your reading of the request win over it.

## Routing table
| Request looks like | Primary skills | Add only if |
|---|---|---|
| Write or change code that will live on | `line-durability`, `myopia-patterns` | money/data: `assumption-ledger`; auth, secrets, personal data, public endpoint: `security-durability`; hard to undo: `reversibility-check`; deploy, migrate or delete: `rollback-path` |
| Review a pull request, diff or patch, "is this safe to merge" | `diff-review` | AI-written: `ai-code-audit`; dependencies changed: `dependency-risk`; migration or delete: `rollback-path`; API changed: `api-contract-stability` |
| Code written or edited by an AI, "the AI wrote this", "I do not trust generated code" | `ai-code-audit` | line level: `line-durability`; tests: `test-durability`; secrets or input: `security-durability` |
| Change an API, schema, CLI flag or file format others depend on, "will this break clients" | `api-contract-stability` | hard to undo: `reversibility-check`, `rollback-path`; record: `adr-writer`; CI guard: `fitness-functions` |
| Review a function, file or snippet | `line-durability`, `myopia-patterns` | class C/D: `verdict-format` |
| Review or write tests, flaky or slow suite, "tests pass so it is fine" | `test-durability` | before a refactor: `refactor-planner`; debt: `debt-ledger` |
| Audit a repo, take over a project, "rewrite or patch?" | `codebase-longevity-audit` | fixes pile up: `logic-myopia-audit`; debt: `debt-ledger`; plan needed: `refactor-planner` |
| Where code should live, cycles, coupling, split/merge | `module-boundary-review` | `change-injection` to measure |
| Add, upgrade or choose a library or vendor | `dependency-risk` | lock-in: `reversibility-check` |
| "Should we add X (plugin, abstraction, config)?", "can we add X easily?" | `extensibility-review`, `change-vectors` | torn or costly: `council-protocol`; class A/B: TEMPORARY IS ENOUGH only |
| Design or review a service, data model, API, pipeline, integration | `system-design-longevity`, `failure-and-scale-modes` | one-way doors: `reversibility-check`, `adr-writer`; no design text: INSUFFICIENT EVIDENCE |
| Choose a database, schema, public API, vendor, anything hard to undo | `reversibility-check`, `three-horizon-map` | `rollback-path` for the way back; `adr-writer` to record |
| "What are we assuming?", result looks too certain | `assumption-ledger` | `assumption-tripwires` for risky ones |
| Shortcut, quick fix, technical debt | `debt-ledger` | `refactor-planner` for payoff |
| Turn a decision into a CI rule | `fitness-functions` | `adr-writer` |
| Can a stranger understand this code? handover | `archaeology-test` | |
| Will the money last, budget, runway, retirement, savings | `long-horizon-cashflow` | `scenario-stress-test`; `assumption-sensitivity` if inputs are uncertain |
| Plan or loan breaks under bad events | `scenario-stress-test` | `long-horizon-cashflow` for the base model |
| Business case, ROI, pricing, "which input matters" | `assumption-sensitivity` | `scenario-stress-test` |
| Portfolio, drawdown, leverage, ruin | `tail-risk-review` | `scenario-stress-test` |
| Hard choice under uncertainty (buy vs wait) | `decision-regret-check` | `assumption-sensitivity` |
| UI styling, colours, spacing, theming, dark mode | `design-token-discipline` | `consistency-audit` |
| UI looks patched together, before a redesign | `consistency-audit` | `design-token-discipline` |
| Shared component props or UI library release | `component-api-stability` | |
| Accessibility, platform or browser drift | `accessibility-and-platform-drift` | |
| Record a forecast to check later, reliability of past verdicts | `calibration-loop` | |
| One-off script, throwaway, prototype under 3 months, one user | none beyond `horizon-fit` | TEMPORARY IS ENOUGH path |

## Mandatory header (first lines of every routed answer)
```
ROUTE: <skill1 -> skill2 -> ...> | skipped: <skill: reason; ...>
CLASS: <A|B|C|D> [PROVISIONAL] | Components escalated: <none | component -> class, ...>
```
No header means not routed. For class A/B the ROUTE line is `horizon-fit` only.

## Failure patterns
| Pattern | Fix |
|---|---|
| Money question answered from general knowledge | Finance skills; state compounding and indexing conventions |
| Review of something not shown | INSUFFICIENT EVIDENCE with needed inputs |
| Ceremony for a small job | Class A/B exit path, one safeguard at most, tied to a named failure cost |
| All skills named | Cap of 4, each justified |
| Skill named but not applied | List only skills whose output you used; unrun scripts get `NOT MEASURED` |
| Unstated fact assumed (internal vs public, one state vs many) | Give both branches, name the deciding fact |
| Code delivered without saying whether it ran | End with `Not run.` or the test result |

## Exit path
- **Missing input:** request too vague to route: ask one question, or route to `horizon-fit` only.
- **Script problem:** if `route.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** if a chosen skill turns out not to apply, drop it, say so in the ROUTE line, and carry on.

## Limits
`route.py` is a keyword heuristic; its cases (`templates/route_cases.json`) cover only what has been written. Add a case whenever a request is routed wrongly.
