# Round 4 results (Haiku 5.5, medium effort)

Tasks: `benchmarks/judge/ROUND4_PROMPTS.md`. Hidden notes: `ROUND4_JUDGE.md`. Rubric: `JUDGE.md` (6 criteria, 0-2 each, max 12 per task). A = no skill, B = AGENTS.md and skills loaded. Raw answers are in this folder. Judge: the task author, one pass, not blind.

| Task | Run 1 A | Run 1 B | Run 2 A | Run 2 B |
|---|---|---|---|---|
| H1 SMS demo | 6 | 8 | 6 | 9 |
| H2 checkout review | 5 | 10 | 4 | 11 |
| H3 retirement (computed, ground truth 308 / 204) | 9 | 11 | 8 | 12 |
| H4 rewrite in Go | 5 | 12 | 5 | 12 |
| H5 drop column | 6 | 10 | 7 | 11 |
| H6 standup script | 7 | 8 | 7 | 12 |
| **Total /72** | **38** | **59** | **37** | **67** |

Mean: A 37.5, B 63, gap +25.5. The Format criterion favors B by construction (A does not know the output shape); without it the mean gap is about +13.5.

## Observations
- Largest gaps: H4 (A gave a flat "No"; B returned INSUFFICIENT EVIDENCE) and H2 (A had no `file:line` or verdict).
- H3: both found month 204 for the shock case; A's base case was month 309 (truth 308, stated as approximate), B ran code and matched 308, 204, 314, 206 (rechecked).
- Repeated B errors, fixed afterwards in `horizon-fit`, `AGENTS.md` and the line-number rule: whole demo classed C when one component was escalated (H1); line numbers offset by 13 in H2 (counted from the prompt file); class C for a one-user script (H6, run 1 only).
- Flags: A mentioned `MAX_RETRIES` as unused in both runs (F5 borderline); A stated a month without a method in run 2 (F6 borderline). B: none.
- In run 2, B's H1 and H6 code was written to files that were not part of the pasted answer, so that code was not checked.

## Limits
Two runs per condition, one model, author as judge, same tasks seen by the author before the run. An indicator, not proof. The skill changes made after this round were not re-measured; use a new task set.

## Run 3: Sonnet 5.5, low effort (patched skills)
Files: `run3_sonnet-low_A_no_skill.md`, `run3_sonnet-low_B_with_skill.md`.

| Task | A | B |
|---|---|---|
| H1 | 7 | 11 |
| H2 | 5 | 11 |
| H3 | 8 | 11 |
| H4 | 5 | 9 |
| H5 | 7 | 11 |
| H6 | 7 | 11 |
| **Total /72** | **39** | **64** |

Gap +25 (about +14 without the Format criterion). Rechecked by running: H3 months 308, 204, 314, 206 and the shortfalls ($471, $1,700) are correct; `scan_line_risks.py` gives 11 candidates and `scan_security.py` 1 medium on the H2 snippet; `round(10*1.0825, 2)` is 10.82.
- B: class split worked (H1 `CLASS: B` with escalated components); H2 lines counted from `import requests` and match the judge key; H5 has ONE-WAY, restore point, trigger and point of no return.
- B errors: H4 never named idempotency and listed `codebase-longevity-audit` without applying it (routing error); H3 "at most $1,576/month" and "$952,077" are off by about one unit (1,576 still ends at -$571 at month 360); H6 left the webhook URL in the file; H1 code was in a file not shown.
- A (Sonnet low, no skill): exact H3 numbers, but no method stated; H2 had no line numbers or verdict; H4 a flat "No"; H5 and H6 no ONE-WAY / re-class trigger.
