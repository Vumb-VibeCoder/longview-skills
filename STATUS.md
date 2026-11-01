# STATUS v3

Language: English only. A skill is READY only when its text is in English, its procedure is internally consistent, and any bundled script has been executed on test inputs.

| Skill | Status | Notes |
|---|---|---|
| core/skill-router | READY (v3.1) | route.py + 31 regression cases (tests were written after seeing early failures, so the pass rate is not an unbiased accuracy); routing table covers all skills (validator-enforced); mandatory ROUTE/CLASS header in AGENTS.md |
| core/* (10 others): horizon-fit, verdict-format, myopia-patterns, assumption-ledger, assumption-tripwires, council-protocol, three-horizon-map, calibration-loop, change-vectors, reversibility-check | READY (v3, English) | unified ledger schema (confidence, impact, expiry, owner); tripwire_check.py rewritten and tested; calibration_report.py added and tested; council formula corrected (benefit = P x (C_late - C_prepared) vs C_prep + C_carry) |
| coding/module-boundary-review | READY (v3) | scripts: module_graph.py, cochange.py (tested) |
| coding/dependency-risk | READY (v3) | script: dep_scan.py (tested) |
| coding/fitness-functions | READY (v3) | script: check_rules.py + rules.example.json (tested incl. mutation) |
| coding/archaeology-test | READY (v3) | script: prepare_blind_copy.py (tested) |
| coding/adr-writer | READY (v3) | template + adr_lint.py (tested on good, bad and superseded ADRs) |
| coding/line-durability, change-injection, debt-ledger, codebase-longevity-audit, logic-myopia-audit, refactor-planner | READY (v3, English) | scan_line_risks.py rewritten (fewer false positives, dedup, M05/M06); debt_calc.py with ledger mode, margin and residual interest; blast_radius.py, hotspots.py, plan_check.py added; all executed on test inputs |
| finance/long-horizon-cashflow, scenario-stress-test | READY (v3) | cashflow.py + model.example.json (tested: base, shocks, exit code 1 on failure, missing-field error) |
| finance/assumption-sensitivity | READY (v3) | sensitivity.py (tested: break-even checked by hand, decision-flip detection, formula-injection rejected) |
| finance/tail-risk-review | READY (v3) | tail_stats.py (tested on fat-tail and calm series; false alarm on calm series found and fixed by raising the CVaR ratio threshold to 1.3) |
| finance/decision-regret-check | READY (v3) | regret.py (tested: conflict detection, bad-shape error) |
| design/* (3) | READY (v3) | procedure-only skills, no scripts; cross-references checked |
| ui/design-token-discipline, consistency-audit | READY (v3) | ui_scan.py (tested on seeded CSS/TSX: token files and comments skipped, px/unitless font sizes unified, near-duplicate colors found) |
| ui/component-api-stability | READY (v3) | props_diff.py (tested: breaking, safe-only, unchanged, missing-type; two parser bugs found and fixed: `=>` miscounted as a bracket, comment regex swallowing following props) |
| ui/accessibility-and-platform-drift | READY (v3) | procedure-only |
| benchmarks/ (miner, prepare_prompts, run_api, score), README.md, templates/SKILL.template.md | v3 English | miner/prepare_prompts/score tested end-to-end on a synthetic git repo (reverts, patched commits, clean controls, no answer leakage in prompts or file names, error answers counted as missing); run_api.py NOT tested on the real API; no real benchmark results yet |

Vocabulary in v3: verdicts are KEEP, REINFORCE, REWRITE, TEMPORARY IS ENOUGH and INSUFFICIENT EVIDENCE (the last one is new; earlier drafts used different names).

Promotion rule PLANNED -> READY: the skill must improve benchmark scores versus an AI not using it (when benchmark data exists), and pass the consistency checks above.

## Install
- claude.ai: upload each file in `dist/` at Settings > Capabilities > Skills.
- Claude Code: copy the skill folder into `.claude/skills/`.

## Tooling
- `tools/validate_repo.py [--build]`: frontmatter, English-only, cross-references, referenced scripts/templates exist, Python compiles. Mutation-tested (missing script, unknown skill, Vietnamese text each caught).
- `benchmarks/git-history-miner/review_labels.py` + `score.py --verified-only`: human label review (tested on real mined cases).
- `EXAMPLE.md`: worked example; scanner output is real, scores are judgment following the rubric.
- Miner v2: filters for bot/lockfile/CI/docs noise, added after a run on qdrant/migration. 12 cases mined there; labels not yet human-reviewed; no AI scoring has been run.

## v3.1 patch (from the first A/B judging round)
Trigger: Haiku 5.5, 6 tasks, with-skill scored 46/72 vs 30/72 without; gains were in judgment tasks, near zero on money tasks (finance skills not triggered) and the with-skill answers often skipped the class line.
Changes: skill-router (new), mandatory ROUTE/CLASS header, TEMPORARY IS ENOUGH block (Do / Safeguard / Debt / Re-class trigger), INSUFFICIENT EVIDENCE shape, finance descriptions rewritten around the questions people actually ask, cashflow conventions (compounding, indexed withdrawals, NOT MEASURED), line-durability findings require file:line + M-ID, junk folder removed. Round 2 (+31) and round 3 on new tasks (+30) are in `benchmarks/RESULTS.md`.

## v3.2 patch
From round 3: ROUTE lists only skills actually applied (visible trace required), unrun scripts are marked NOT MEASURED, unstated deciding facts get both branches, unexecuted code ends with `Not run.`. Not yet re-tested.

## v3.3 clarity pass
Found by review: (1) class horizons disagreed (change-vectors said 3-5 years for D, verdict-format 5): now defined once in horizon-fit with the LOW/MEDIUM/HIGH probability scale, referenced elsewhere; (2) cashflow.py could not model investment return, so the most common question (will savings last) had to be computed by hand: added return_annual, return_compounding (mandatory, so the convention is explicit) and expense_indexing, plus templates/retirement.example.json and a validator regression against the hand calculation; (3) AGENTS.md process list read as mandatory for every request: now labelled the maximum; (4) exit-path block was three lines in AGENTS.md and four in horizon-fit: aligned. Not re-tested with an AI.
