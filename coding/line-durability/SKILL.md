---
name: line-durability
description: Judge whether individual lines and functions of code will survive change: hard-coded values, swallowed errors, hidden assumptions about size/order/environment, duplication, and unexplained oddities, with severity by probability and consequence. Use when writing or reviewing code that must live long (class C/D). Ships a Python scanner that lists measurable candidates.
metadata:
  domain: coding
  status: READY
---
# Line Durability: will this line survive?

Line-level review. It finds candidates by measurement, then confirms them by reading. It does not judge architecture (see `module-boundary-review`) or business logic (see `logic-myopia-audit`).

## When to activate
Writing or reviewing code of class C/D (run `horizon-fit` first). For class A/B with no escalator, check only correctness and the escalated parts.

## Required inputs
The code, plus its context: who calls it, where input data comes from, what happens on failure. If context is missing, ask.

## Procedure
1. **Measure (Python):** `python scripts/scan_line_risks.py <path>`. It lists CANDIDATES for M01, M03, M04, M05 (including network calls with no timeout), M06, M08, M12 (float arithmetic on money-named values) and TODO notes. For other languages, skip the script and apply step 2 by reading; say the scan was not run.
2. **Read each candidate and the surrounding code**, asking five questions:
   1. Is a value, string, path, currency or URL hard-coded in logic? (M01)
   2. What does it assume about data size, ordering, timing or environment? (M05, M06)
   3. Where does an error go? Is it swallowed or ignored? (M03)
   4. To change this, must other code change too? (M07)
   5. Would a stranger understand **why** it is like this in 12 months? (M09)
3. **Discard false positives** using the "Do NOT flag when" column of `myopia-patterns` (a named constant, a documented exception, bounded input). Report how many candidates were discarded.
4. **Also read what the scanner cannot see:** missing validation at boundaries, missing timeouts on I/O, missing tests for the failure path, time/locale handling.
5. **For every confirmed finding record:** `file:line`, pattern ID, concrete consequence, severity, smallest fix.
6. **Severity** (probability that the trigger occurs within the class horizon (defined in `horizon-fit`; LOW < 20%, MEDIUM 20-60%, HIGH > 60%) x consequence if it does):
   - **MUST FIX:** probability MEDIUM or higher AND consequence of days of work, data/money/security loss, or silent wrong results
   - **SHOULD FIX:** probability MEDIUM+ with a small consequence, or LOW probability with a large consequence
   - **ACCEPTABLE:** LOW and small. Record in `debt-ledger` only if it has real interest.
7. **Do not add abstraction for something that has appeared once** (M10). Three occurrences justify extraction (M04). If unsure whether to fix or leave, run `council-protocol`.
8. If the user wants a verdict, this skill supplies evidence for **Assumption fragility**, **Operability** and part of **Change tolerance**. The other dimensions have no line-level evidence, so a verdict from this skill alone would hit `verdict-format` rule 2 (INSUFFICIENT EVIDENCE). Say so instead of inventing scores.

## Output
| Location | Pattern | Consequence | Severity | Smallest fix |
Every row needs `file:line` (use `snippet:line` when no file name exists) and a pattern ID (M01-M12) from `myopia-patterns`; a row without both is a question, not a finding. Do not flag true constants (0, 1, 100 percent, HTTP 200). Count lines from the first line of the code as it was given to you (that line is 1), never from the surrounding message or file; when the code has no line numbers, say `snippet:line` and count it yourself.
Plus: candidates found / confirmed / discarded, and what was not examined.

## Exit path
- **Missing input:** no code supplied: ask for the file; do not review from a description.
- **Script problem:** if `scan_line_risks.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** for throwaway code (class A/B) stop after the correctness check.

## Limits
The scanner catches syntax-level patterns in Python only; it flags candidates, not defects. Logic errors, business assumptions and security flaws need reading and domain knowledge.
