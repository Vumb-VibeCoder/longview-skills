# Benchmark results: judged A/B rounds

Two kinds of benchmark exist in this repo:
1. **Git-history benchmark** (`git-history-miner`, `runner`, `scoring`): measures whether skills help find code that was later reverted or patched. No scored run exists yet.
2. **Judged A/B rounds** (this file, `judge/JUDGE.md`): the same task is given to an AI without the skills (A) and with them (B), and a judge scores both on six criteria, 0-2 each (max 12 per task).

## Method
- Judge: Claude, scoring A and B from pasted answers. Criteria: fit to the horizon class, evidence, output format, honesty, decision rule, economy.
- Model under test: Haiku 5.5 (medium effort), both conditions.
- Numbers and script claims in the with-skill answers were re-computed by the judge before scoring honesty.

## Results
| Round | Tasks | A (no skills) | B (with skills) | Effect | Skills version |
|---|---|---|---|---|---|
| 1 | T1-T6 | 30/72 | 46/72 | +16 | v3 |
| 2 | T1-T6 (same tasks, patched skills) | 33/72 | 64/72 | +31 | v3.1 |
| 3 | S1-S6 (new tasks) | 32/72 | 62/72 | +30 | v3.1 |

Round-3 per task (A / B): S1 6/11, S2 5/12, S3 2/12, S4 6/8, S5 7/9, S6 6/10.

## What the rounds showed
- **Round 1:** gains came from judgment tasks (stopping, refusing, missing evidence). Money tasks showed almost no skill effect because the finance skills were not triggered. The with-skill answers often omitted the class line.
- **Patch v3.1:** added `core/skill-router`, a mandatory ROUTE and CLASS header, the TEMPORARY IS ENOUGH block, the INSUFFICIENT EVIDENCE shape, finance descriptions written around real questions, and cashflow conventions.
- **Round 2:** every with-skill answer carried the header and used the right skills. Part of the gain is likely tuning to these exact tasks, because they were also the routing test cases.
- **Round 3:** new tasks gave nearly the same effect, so the gain was not only memorisation. Remaining weaknesses: skills named in ROUTE but not applied (S4), an unstated assumption chosen silently (S5), code delivered without saying it was not run (S1). Patch v3.2 targets these three.

## Caveats (read before quoting any number)
- One run per task, six tasks per round, one model. Treat the effect as an indicator, not proof.
- The judge saw the with-skill format and may favour it; scores should be spot-checked by a second judge or a human.
- The A chat in round 3 was not fresh (it referred to an earlier answer), so A may be slightly inflated.
- The judge also wrote the rubric and the tasks.
- Nothing here shows the skills help with larger real-world work; that needs the git-history benchmark on a repo with real history.

## Reproduce
Follow `judge/JUDGE.md`. Use a fresh chat per task and condition, then score with the rubric there.
