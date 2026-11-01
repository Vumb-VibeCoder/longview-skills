---
name: test-durability
description: Judge whether a test suite will still protect the code in one, three and five years - tests that never fail, tests that break on every refactor, flaky or slow tests, tests that depend on the clock, network, order or a mocked-away reality, and gaps around the code that matters most. Use when reviewing or writing tests, before a refactor or migration, when a suite is flaky or ignored, or when "all tests pass" is being used as proof. Ships a pattern scanner and a test plan template.
metadata:
  domain: coding
  status: READY
---
# Test Durability: tests that still work, and still mean something, years later

Every other safety step depends on tests: `refactor-planner` starts with characterization tests, and `rollback-path` assumes you can tell when something broke. A suite that is flaky, slow or tied to implementation details gets ignored, and then it protects nothing. This skill checks the suite itself.

## When to activate
Class C/D code (`horizon-fit`), before any refactor or migration, when someone says "the tests pass so it is fine", or when the team has stopped trusting the suite. For class A/B, one test of the main behaviour is enough.

## Required inputs
The test files, how to run them, and what the code is for. If you cannot run the suite, say so; static review alone cannot show flakiness or speed.

## Procedure
1. **Run the scanner:** `python scripts/scan_tests.py PATH`. Confirm each finding by reading the test, and mark false positives with a reason.
2. **Make a map.** List the behaviours that would hurt most if they broke (money, data, security, the public interface). Mark which have a test. The untested ones, not the coverage percentage, are the gaps.
3. **Check that tests can fail.** For two or three important tests, break the code on purpose (flip a condition, return a wrong value) and confirm the test goes red. A test that stays green proves nothing. Undo the change afterwards (`rollback-path`).
4. **Check for flakiness.** Run the suite at least three times, once in random or reversed order. Anything that changes result is a defect to fix or quarantine with an owner and a date.
5. **Check how it will age.** Look for the five things that rot: the real clock and hard-coded dates, live network or third-party services, shared state and test order, snapshots nobody reads, and unpinned test tooling. Each one is a test that will fail for no reason in a year.
6. **Check what it is coupled to.** A good test survives an internal refactor. If renaming a private method breaks ten tests, they describe the implementation, not the behaviour. Prefer testing through the public interface.
7. **Check mocks.** Mock the edges (network, clock, disk) and keep the logic real. When mocks outnumber assertions, the test may only check the mocks.
8. **Check speed and feedback.** Record the run time. A suite that takes long enough that people skip it will be skipped. Separate fast tests from slow ones.
9. **Check what happens to failures.** Every past bug should have a test that would have caught it. Skipped tests need an owner and a date (`debt-ledger`). Deleting a test needs a stated reason.
10. **Record the plan** with `templates/test-plan.example.md`, and turn the rules that can be automated into `fitness-functions` (for example "no `sleep` in tests").

## Mandatory questions
- If the most important behaviour broke tonight, which test would fail first?
- Has anyone seen that test fail for a real reason?
- Which tests would fail next January or next leap year for no reason related to the code?
- How long does the suite take, and does everyone run it?
- What is skipped, since when, and who owns it?

## Output
Findings ranked by severity with `file:line`, then the map of important behaviours with and without tests, the flakiness and speed results (or `NOT MEASURED`), and a short ordered plan. Use `verdict-format` for a class C/D verdict. Coverage percentages may be quoted, never used as the verdict.

## Exit path
- **Missing input:** no tests exist: say so, and propose the smallest set that guards the important behaviours (this feeds `refactor-planner`). If tests exist but cannot be run, review statically and label every runtime claim `NOT MEASURED`.
- **Script problem:** if `scan_tests.py` exits 2 or crashes, fix the path once and retry. If it still fails, write `NOT MEASURED: scan_tests.py` and review by hand. A scan that finds no test files may only mean an unusual naming scheme; ask before concluding that there are none.
- **Stop or hand off:** if step 3 shows an important test cannot fail, stop and fix that before any refactor. If the suite is too broken to trust, do not use it as a safety net: write characterization tests first (`refactor-planner`) and note the debt.

## Limits
The scanner reads patterns, not meaning. It cannot tell whether an assertion is the right one, whether the tests cover the right behaviour, or how long the suite takes. It checks Python, JavaScript, TypeScript and Go file names and patterns only. Breaking code on purpose (step 3) is a spot check, not full mutation testing. Coverage tools and real runs remain necessary.
