---
name: diff-review
description: Review one change - a pull request, commit range or patch - instead of a whole codebase. Checks that the change matches its stated intent, is small and focused enough to review, is covered by tests, has a way back, and does not quietly add dependencies, weaken tests or leave debug code, secrets and TODOs behind. Use when someone says "review this PR", "review this diff", "is this safe to merge", "check my changes" or pastes a diff. Ships diff_stats.py, which measures a unified diff and raises flags D01 to D08.
metadata:
  domain: coding
  status: READY
---
# Diff Review: is this change safe to merge, and is it only what it claims to be?

Review of a single change. It starts from the intent, measures the diff, reads the tests before the code, and ends in a clear outcome. It does not audit the whole codebase (see `codebase-longevity-audit`) or judge each line in depth (see `line-durability`).

## When to activate
A diff, pull request, patch or commit range is on the table, and someone wants to know whether to merge it. Run `horizon-fit` first. For class A/B with no escalator check only that it is correct, small and reversible, and stop.

## Required inputs
1. The diff itself (`git diff`, `git show`, a .patch file or pasted text).
2. The intent: the PR description, ticket or the request that caused it. If missing, ask for one sentence; without it only the mechanical flags can be reported.
3. How it was tested: the command and its result, or a statement that it was not run.

## Procedure
1. **State the intent** in one sentence and the class of change: feature, fix, refactor, dependency, migration, docs. A change that claims to be a refactor must not change behaviour.
2. **Measure:** `python scripts/diff_stats.py <diff-file>` (or `--git <range>`, or pipe the diff in). It reports size per category and flags D01 to D08 (table below). Do not review a diff without this step when a shell is available.
3. **Size and focus (D02, D03).** If the change is too large or mixes concerns, the first finding is SPLIT: name the cut lines (for example "dependency bump", "rename", "behaviour change"). Do not review what cannot be held in one head.
4. **Read the tests first.** Do they describe the new behaviour? Would they fail on the old code? Were assertions removed, tests skipped or expectations edited to match new output (D06)? Source changes with no test change (D01) need a stated reason.
5. **Read the source against the intent.** Everything the diff does beyond the intent is scope creep: list it. Everything the intent implies that the diff does not do is a gap: list it.
6. **Ask the risk questions** and hand off only where a flag or a finding calls for it:
   - new or changed dependency (D04) -> `dependency-risk`
   - migration, schema, delete, deploy (D05) -> `rollback-path`
   - public API, schema, CLI flag or file format changed -> `api-contract-stability`
   - secrets, input handling, permissions (D07) -> `security-durability`
   - written by an AI assistant -> `ai-code-audit`
   - lines that will not survive change -> `line-durability`
7. **Check the debris (D07, D08):** debug prints, bare except, TODOs without an owner, generated files, lockfile changes with no reason. Each is either removed or recorded in `debt-ledger`.
8. **Choose the outcome** with the rule below (first match wins).

## Outcome rule
1. No diff, or no intent and no way to infer it: INSUFFICIENT EVIDENCE.
2. Any MUST FIX finding (security hole, data loss risk, no way back for a one-way step, broken contract with no migration path, tests weakened to pass): CHANGES NEEDED.
3. D02 or D03 raised and the concerns are separable: SPLIT.
4. Only SHOULD FIX findings: MERGE WITH FOLLOW-UPS, each follow-up recorded in `debt-ledger` with an owner.
5. Otherwise: MERGE.
These are review outcomes for one change. Use `verdict-format` only when the user wants a scored verdict for a class C/D change.

## Flags
| ID | Meaning |
|---|---|
| D01 | Source changed, no test file changed |
| D02 | Too large to review as one change (over 400 changed lines or 15 files by default) |
| D03 | Touches four or more top-level areas |
| D04 | Dependency manifest changed, or manifest and lockfile out of step |
| D05 | Migration, schema or SQL file touched |
| D06 | Tests weakened: file deleted, assertions removed, skip or xfail added |
| D07 | Risky lines added: bare except, TODO, debug leftovers, hard-coded secret, TLS off, eval or exec |
| D08 | Generated or build output in the diff |

## Mandatory questions
- What is the intent, and which lines of the diff serve it?
- Which test fails if the main change is reverted?
- If this is deployed and goes wrong, what is the way back and who triggers it?
- Is anything in the diff not explained by the intent?

## Output
Outcome line first, then a table: `Location | Flag or pattern | Finding | Severity | Required change`. Every row needs `file:line` from the diff's new-file side (use `snippet:line` for pasted text and count from its first line). Add: what was measured (`diff_stats.py` result) or `NOT MEASURED: diff_stats.py`, what was run (`Not run.` if nothing), and what was not reviewed. See `templates/sample.diff` for a diff that raises most flags.

## Exit path
- **Missing input:** no diff: ask for it; never review from a description. No intent: ask for one sentence, report mechanical flags only, and do not give MERGE.
- **Script problem:** if `diff_stats.py` exits 2, check that the input is a unified diff (it must contain `diff --git` lines) and retry once. If it still fails, write `NOT MEASURED: diff_stats.py`, count changed files and lines by hand, and carry on. Exit code 1 only means flags were raised.
- **Stop or hand off:** stop at SPLIT or INSUFFICIENT EVIDENCE without reviewing line by line. For a whole-repo question use `codebase-longevity-audit`.

## Limits
`diff_stats.py` reads text only: it cannot judge whether the logic is right, whether tests are meaningful, or whether a renamed file hides a real change. File categories are guessed from paths and may be wrong in unusual layouts. Added-line checks are regex candidates and can misfire on strings or comments. A diff shows what changed, not what the surrounding code already did wrong.
