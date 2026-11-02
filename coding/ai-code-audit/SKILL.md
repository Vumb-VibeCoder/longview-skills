---
name: ai-code-audit
description: Audit code written or edited by an AI assistant for the mistakes AI makes most often - packages and functions that do not exist, placeholder stubs, tests that cannot fail, claims of success that were never run, extra scope nobody asked for, and abstractions with one user. Use before merging or accepting AI-generated code, when someone says "the AI wrote this", "Copilot/ChatGPT generated it", or "it looks right but I do not trust it". Ships a Python scanner (scan_ai_risks.py) for invented imports and stdlib attributes, stubs, empty tests and unused imports.
metadata:
  domain: coding
  status: READY
---
# AI Code Audit: does this code exist, run, and do only what was asked?

AI-written code fails in ways human code rarely does: it looks fluent and complete while calling things that do not exist, leaving stubs behind, and passing tests that test nothing. This skill checks those failure modes by measurement and by running the code, not by reading it and feeling reassured.

## When to activate
Code, a diff or a repo that an AI wrote or edited, before it is merged, shipped or built on. Works for any `horizon-fit` class, but scale the effort: for class A/B run only steps 1 to 3 (does it exist, does it run). For class C/D run all steps. For a pull request as a whole, route to `diff-review` first and use this skill on the AI-written parts.

## Required inputs
The code (file or folder), the dependency manifest (requirements.txt, pyproject.toml, package.json), the original request given to the AI, and the tests if any. If the original request is missing, ask for it: scope cannot be judged without it.

## Procedure
1. **Measure (Python):** `python scripts/scan_ai_risks.py <path>`. It lists CANDIDATES for A01 to A06 (table below). For other languages skip the script, apply the table by reading, and say the scan was not run.
2. **Existence check (A01, A02).** For every external package, function, method, CLI flag, config key and API endpoint the code uses, confirm it exists in the version actually declared. Use the installed package, its official documentation or its source; never memory. The scanner only checks standard-library names and whether imports are declared, so third-party method names are on you. One invented call that sits on an error path can stay hidden for months.
3. **Execution check (A08).** Run the tests and the entry point. Record the exact command and its result. "Should work" and "tests pass" without a command and output count as not run: write `Not run.` Never claim a run that did not happen.
4. **Intent check (A07, A09).** Restate the request in one sentence. List what the code does beyond it (extra files, new dependencies, renamed things, new layers) and what it fails to do that the request implied. Check that expected values in tests come from the requirement and not from the code's own output.
5. **Test honesty (A04).** For each test ask: would it fail if the code were wrong? Prove it on a scratch copy by breaking one operator or return value in the code under test and running the test again. A test that stays green is a finding.
6. **Stub and elision check (A03).** Every placeholder, template value and "rest of the code" comment must be implemented or recorded in `debt-ledger` with the date it will be removed.
7. **Convention and reuse check (M04).** Compare with two or three neighbouring files: naming, error handling, logging, configuration. Search the repo for an existing helper before accepting a new one; AI code often rewrites what already exists.
8. **Abstraction check (A05, M10).** An interface, base class or factory with one implementation and no named second use is deleted or inlined. Three occurrences justify extraction, one does not.
9. **Discard false positives** and report how many. Common ones: a declared package whose import name differs from its distribution name, an attribute that exists only on another platform, a deliberate stub with a tracked issue.
10. **Hand off:** line-level findings to `line-durability`, security findings to `security-durability`, test-suite quality to `test-durability`, the change as a whole to `diff-review`.

## Patterns
| ID | Pattern | Found by |
|---|---|---|
| A01 | Import of a package that is not declared, local or standard library (possible invented package) | scanner |
| A02 | Call or import of a name that does not exist (stdlib checked by scanner; others by step 2) | scanner and reading |
| A03 | Placeholder: stub body, template secret, elision comment | scanner |
| A04 | Test that cannot fail: no assertion, constant assertion, skipped, errors swallowed | scanner and step 5 |
| A05 | Abstraction with one implementation (also M10) | scanner |
| A06 | Unused import (leftover from an abandoned approach) | scanner |
| A07 | Scope creep: changes nobody asked for | reading, step 4 |
| A08 | Unverified claim: "tests pass" or "works" with no run | step 3 |
| A09 | Code shaped to the test, not the requirement (hard-coded expected values, special-cased inputs) | reading, step 4 |
| A10 | Error swallowed to make the run pass (also M03) | `line-durability` scan |

## Mandatory questions
- Which external names did you verify exist, and against what (version, source, document)?
- What command did you run, and what was its output? If none: `Not run.`
- Which requirement does each new file, dependency and abstraction trace back to?
- Which test fails if the main function returns a wrong value?

## Output
| Location | Pattern | Evidence | Severity | Smallest fix |
Every row needs `file:line` (or `snippet:line`) and a pattern ID A01 to A10 or M01 to M12. Severity uses the scale in `line-durability`: MUST FIX when probability is medium or higher and the consequence is days of work, lost data or money, a security hole or silent wrong results; SHOULD FIX; ACCEPTABLE.
Then: candidates found / confirmed / discarded; `Verified by running: <command> -> <result>` or `Not run.`; and what was not examined. See `templates/audit-report.example.md`.

## Exit path
- **Missing input:** no code, or no original request when scope is in question: ask for it; do not audit a description of code.
- **Script problem:** if `scan_ai_risks.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: scan_ai_risks.py`, do the existence and stub checks by reading, and quote no counts. Exit code 1 only means candidates were found.
- **Stop or hand off:** if the code is throwaway (class A/B) stop after steps 1 to 3. If everything found is ACCEPTABLE, say so and stop.

## Limits
The scanner reads Python only and checks standard-library names against the interpreter that runs it, so platform- or version-specific attributes can be false positives. It cannot tell whether a third-party method exists or whether the logic is right. A clean scan means none of these six patterns was detected, not that the code is correct. Running the code, step 3, is the strongest check and cannot be replaced by the scanner.
