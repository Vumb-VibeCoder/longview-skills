# STATUS v3

Language: English only. A skill is READY only when its text is in English, its procedure is internally consistent, and any bundled script has been executed on test inputs.

| Skill | Status | Notes |
|---|---|---|
| core/skill-router | READY (v3.1) | route.py + 38 regression cases (tests were written after seeing early failures, so the pass rate is not an unbiased accuracy); routing table covers all skills (validator-enforced); mandatory ROUTE/CLASS header in AGENTS.md |
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

## v3.4 patch (self-audit with the skills' own method)
- `cashflow.py`: rejects unknown model/scenario keys (a typo like `income_shok` used to be ignored and gave a false OK); input errors exit 2, a failed `must_survive` scenario exits 1. The copy in `scenario-stress-test` was stale (ignored `return_annual`) and is now identical.
- `sensitivity.py`: no more `eval`; exponent limit; clean exit 2 on bad formulas. `regret.py`, `tail_stats.py`, `check_rules.py`, `adr_lint.py`, `calibration_report.py`: no tracebacks on unreadable input.
- All text `open()` calls now pass `encoding="utf-8"` (not tested on Windows).
- `verdict-format`: REWRITE gate added so it no longer contradicts `codebase-longevity-audit`.
- `tools/validate_repo.py`: same-named scripts must be identical; `dist/` must match sources.
- New `tests/test_regression.py` (17 tests; spot mutation-checked on 4 deliberate breaks). Run: `python3 tests/test_regression.py`.
- Known and accepted: the router still does well mainly on phrases it was written around (4/12 on fresh questions in the audit).

## v3.5 additions
- New `coding/rollback-path`: every deploy, migration, delete or schema change gets a restore point, a way back, a trigger and a stated point of no return. Procedure and template only, no script.
- Every skill has an `## Exit path` section; `AGENTS.md` has a shared "When something goes wrong" block. The validator enforces the section.
- New `coding/security-durability` with `scan_security.py` (SEC01-SEC10 pattern rules, secrets masked in output) and a threat model template. First of the planned gaps: next are test quality and operability.
- New `coding/test-durability` with `scan_tests.py` (TST01-TST09: no assertion, sleeps, network, clock and fixed dates, skips, unseeded randomness, mock-heavy files, private-member asserts) and a test plan template. Next planned: operability.

## v3.6 additions
- `benchmarks/git-history-miner/miner.py` v2: positives come from `git blame` on the fix's parent (the fix must rewrite lines the candidate introduced), housekeeping commits and non-code files are ignored, size window 3-400 added lines. On pallets/click: 499 -> 60 positives. Two regression tests (one mutation-checked). Labels not yet human-reviewed; no model-scored run exists.
- Gaps found by running the process on a small order-total function (a live-shop example): `scan_security.py` now flags plain `http://` endpoints (SEC10, loopback and XML-namespace URLs excluded); `scan_line_risks.py` now flags network calls without a timeout (M05) and float arithmetic on money-named values (M12, new pattern in `myopia-patterns`). Heuristics: they find candidates and will miss aliased imports and money values with unusual names.
- Human review of 20 mined positives on pallets/click (subject, fix and overlapping removed lines read; full diffs not read): 10 valid, 9 invalid, 1 unclear. Main false positives were doc/style/test-housekeeping fixes and reverts that touched a different commit's lines; the fix-subject and commit-subject filters were tightened afterwards (not re-reviewed). Still no model-scored run.
- Router: code that makes network calls (requests.get, urlopen, fetch, http://) now suggests `security-durability`; two new routing cases (40 total).

## Round 4 follow-up (small-model run, 2 runs, Haiku 5.5 medium; all rounds in `benchmarks/RESULTS.md`)
Mean score A (no skill) 37.5/72, B (with skill) 63/72 (raw answers and per-task scores: `benchmarks/results/round4/`); without the Format criterion the gap is about +13.5. Judge was the author of the tasks, one model, two runs each: an indicator, not proof.
Changes made from the repeated B errors: a throwaway with one escalated component is no longer printed as class C for the whole project (`horizon-fit` step 4 and the CLASS line); own-use scripts with no end date stay class B; line numbers count from the first line of the code as given. Not re-measured after these changes; they need a fresh task set.

## v3.14 patch (after Sonnet 5.5 low run)
- `long-horizon-cashflow`: reverse-stress thresholds must be rounded safely and re-run at the printed value (run 3 printed $1,576 and $952,077, both still ending below zero).
- `verdict-format`: INSUFFICIENT EVIDENCE gets a `Fix now` line for known control gaps (run 3 never named idempotency in H4).
- `horizon-fit`: a secret goes in an environment variable even in class B (run 3 left the H6 webhook in the file).
- README: badges, shorter intro, status text updated to four rounds. Not re-measured.
