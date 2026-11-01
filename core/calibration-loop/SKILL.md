---
name: calibration-loop
description: Record falsifiable predictions made during reviews and later compare them with what actually happened, computing a Brier score and per-confidence-bucket hit rates. Use after any evaluation that makes a forecast, or when asked how reliable past verdicts were. Ships a report script and a log format.
metadata:
  domain: core
  status: READY
---
# Calibration Loop: learn from being right and wrong

A verdict is worth only as much as the track record behind it. This skill makes the record.

## When to activate
After any class C/D evaluation that states something checkable about the future ("adding X will touch >= 5 files", "module Y will fail beyond Z rows"). Also quarterly, to run the report.

## Procedure
1. **Write 1-3 falsifiable predictions per important verdict.** Each needs: the claim as worded, a **resolution** (how exactly it will be checked and by what source), a `check_on` date, and a confidence.
2. **Confidence means the probability (0.5-1.0) that the claim is TRUE as worded.** If you believe it is less than 50% likely, restate the claim in the opposite direction.
3. **Log one JSON line** in `calibration/log.jsonl` (or the project's equivalent):
   ```
   {"id":"c001","date":"2026-11-01","prediction":"Adding multi-currency requires edits in >=5 files","confidence":0.7,"resolution":"count files changed in the PR that adds a second currency","check_on":"2027-02-01","outcome":null,"notes":""}
   ```
   Where the environment cannot write files (for example a plain chat), print the lines for the user to save. Do not claim they were stored.
4. **Resolve on time:** set `outcome` to `true` or `false` using the stated resolution, not a re-interpretation. Record surprises in `notes`.
5. **Report:** `python scripts/calibration_report.py calibration/log.jsonl`. It lists overdue items, the Brier score (0.25 = coin flip), overconfidence, and per-bucket hit rates.
6. **Act on results:** below 20 resolved predictions the numbers are anecdotes (the script says so). With enough data, consistent overconfidence means lower stated confidence or require stronger evidence before HIGH confidence; a repeated type of miss becomes a candidate for `myopia-patterns` (needs 2 benchmark cases) or an edit to the skill that produced it.

## Mandatory questions
- Could someone else resolve this prediction without asking me what I meant?
- Is this prediction one a different verdict would have contradicted? (If not, it carries no information.)

## Exit path
- **Missing input:** no outcome yet: leave the prediction open and set a check date; do not score it early.
- **Script problem:** if `calibration_report.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** if there are fewer than about 10 scored predictions, report counts only; a Brier score on tiny data misleads.

## Limits
Needs at least 20 resolved predictions, and at least 5 per bucket, before calibration claims mean anything. It measures forecasting quality, not whether a decision was good. Predictions about outcomes the decision itself influenced need care.
