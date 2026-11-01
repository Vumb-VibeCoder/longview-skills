---
name: archaeology-test
description: Test whether code can be understood by a stranger by having a fresh, context-free AI session read it and answer fixed questions, then scoring the answers against the author's ground truth (including confident-wrong answers). Use before declaring code maintainable, after a large refactor, or before a handover of class C/D code. Ships a script that builds the context-free copy.
metadata:
  domain: coding
  status: READY
---
# Archaeology Test: can a stranger read this?

Maintainability claimed by the author is worthless: the author has context. This test uses a reader with none, and measures what they get wrong.

## Hard requirement (read first)
The tester MUST be a **fresh session that has never seen this conversation or the history of the code**: a new Claude Code session or subagent, or a new chat. **The session that wrote or reviewed the code cannot run this test**; it would be contaminated. If a fresh session is not available, say so, give the user the prompt and the blind copy instructions, and stop. Never simulate the reader in the same conversation and report the result as a test.

## When to activate
Class C/D code (run `horizon-fit` first). Before saying "this is maintainable/clear", after a refactor, before handover or open-sourcing.

## Procedure
1. **Build the blind copy:** `python scripts/prepare_blind_copy.py <src> <out>`. It removes git history, markdown/rst docs, ADRs, changelogs and notes; it keeps code, tests, config and in-code comments. Record the printed list as the **test conditions**.
2. **Write ground truth BEFORE the test**, from the author's knowledge, in a file the tester will not see. Answer these six questions:
   - **Q1 Purpose:** what does this code do and for whom (3 sentences)?
   - **Q2 Change:** which files/functions change for the most plausible requirement change? Pick 2 from `change-vectors` and ask them as Q2a, Q2b.
   - **Q3 Invariants:** what must always be true for this code to be correct?
   - **Q4 Failure modes:** what are the 3 most likely ways it breaks in production?
   - **Q5 Surprises:** which parts look wrong or odd but are intentional, and why? (tests M09)
   - **Q6 Dead weight:** what is unused or safe to delete?
3. **Run the tester** with this prompt (and only the blind copy):
   ```
   You are a new maintainer. You have only this repository; nothing else exists.
   Answer from the code alone. For every claim cite file:line.
   If you cannot determine something, write CANNOT DETERMINE; do not guess.
   Give each answer a confidence: HIGH / MEDIUM / LOW.
   Q1 ... Q6 (insert the questions, with the concrete Q2a/Q2b changes)
   ```
4. **Score each question** against ground truth: MATCH = 2, PARTIAL = 1, MISS or CANNOT DETERMINE = 0. Separately count **CONFIDENT-WRONG**: a HIGH/MEDIUM-confidence answer that contradicts ground truth. These are the most dangerous results because the code actively misleads; score them 0 and list them first.
5. **Interpret:** there are seven scored items (Q1, Q2a, Q2b, Q3, Q4, Q5, Q6), so the maximum is 14. Use the percentage of 14:
   - **CLEAR:** >= 80% and zero confident-wrong
   - **PATCHY:** 55-79%, or exactly one confident-wrong
   - **OPAQUE:** < 55%, or two or more confident-wrong
6. **Fix the smallest thing per miss:** rename, a "why" comment, an ADR (`adr-writer`), a test that documents behaviour, deleting dead code. Do not rewrite to please the test.
7. **Re-test with a NEW tester session** (a used tester has learned the answers). For class D use two independent testers; disagreement between them is itself a finding.
8. Use the result as **evidence** for `verdict-format` (Q2 supports Change tolerance, Q3/Q5 support Assumption fragility, Q4 supports Operability). It is not a verdict on its own.

## Mandatory questions
- Did the tester get Q5 right? If the code's intentional oddities are not explained in code, they will be "fixed" by the next maintainer.
- Which answers did the tester get right only because a famous framework made it guessable? (weight project-specific questions more)

## Output
```
Conditions: <removed items> | tester: <tool/session> | date
| Q | Ground truth (short) | Tester answer (short) | Score | Confident-wrong? | Fix |
Result: CLEAR | PATCHY | OPAQUE (<pct>%, <n> confident-wrong)
Smallest fixes in priority order
```

## Exit path
- **Missing input:** no fresh session available: write `NOT MEASURED: blind read` and fall back to `line-durability` on the hardest file.
- **Script problem:** if `prepare_blind_copy.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** if the fresh reader fails the fixed questions, record the score and stop; do not coach the reader.

## Limits
An AI reader approximates but is not a human reader; it measures how explicit the code is, not how elegant. Results depend on the question set and on the author's ground truth being honest. One run is a sample, not a guarantee.
