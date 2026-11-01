---
name: fitness-functions
description: Turn architectural decisions (ADRs, module boundaries, assumptions) into automated CI checks that fail when the decision is violated. Use after a boundary review or ADR, when setting up guardrails for a long-lived (class C/D) codebase, or when a past regression should never recur. Ships a rule runner and an example rule file.
metadata:
  domain: coding
  status: READY
---
# Fitness Functions: decisions that enforce themselves

A decision that lives only in a document decays. This skill converts it into a check that fails the build. It does **not** replace linters (style) or tests (behaviour).

## When to activate
After `module-boundary-review` or `adr-writer`, when a class C/D project wants guardrails, or after an incident where the same structural mistake recurred. Run `horizon-fit` first; class A/B with no escalator: do not create rules.

## Admission test: a rule is accepted only if ALL hold
1. **Has a reason:** it cites an ADR, incident or boundary decision (`why`). No reason, no rule.
2. **Mechanically checkable** with few false positives. Taste and style are rejected.
3. **Green on day one:** existing violations are listed in `allow`, **each tied to a `debt-ledger` entry**. A rule that starts red gets disabled within a week.
4. **Has an owner** who can retire it when the decision is superseded.

## Procedure
1. **Collect candidates** from ADRs, boundary findings, tripwire failures and incident postmortems. Write each as one sentence: "X must not Y, because Z".
2. **Apply the admission test.** Record rejected candidates with the reason.
3. **Choose the mechanism:**
   - `forbid_import`: layering and dependency direction
   - `forbid_pattern`: banned calls (direct env access, raw SQL outside the data layer)
   - `max_file_lines`: size smell guard, only for class D, never as a standalone justification
   - anything else (cycles, API shape, performance budget): write a test in the project's own framework; do not stretch the runner.
4. **Write the rules file** (`templates/rules.example.json` is a model). Every rule: `id`, `type`, `why`, optional `allow` (documented exceptions).
5. **Prove the rules work (mutation check):** run `python scripts/check_rules.py rules.json <repo>`: it must exit 0. Then add a deliberate violation for each rule, confirm it exits 1 and names the right `file:line`, then remove the violation. A rule never seen failing is untrusted.
6. **Wire into CI:** run the same command as a required step; the non-zero exit blocks the merge. Print the `why` in the failure (the runner does).
7. **Maintain:** `allow` entries expire with their debt entry. When an ADR is superseded, delete its rules in the same change. Review the rule list when `calibration-loop` or tripwires show a rule never fires or always fires.

## Mandatory questions
- If this rule fired in a year, would a stranger understand why from the message alone?
- Is the rule guarding a decision, or just freezing today's structure (M09/M10 in rule form)?

## Output
```
Accepted rules: id | statement | why (ADR/incident) | type | allow-list size
Rejected candidates: statement | reason
Mutation check: id | baseline exit 0 | injected-violation exit 1 | location reported
CI line: <the exact command>
```

## Exit path
- **Missing input:** no rule source (ADR or boundary): ask for the decision to enforce first.
- **Script problem:** if `check_rules.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** if a rule has too many false positives to run in CI, mark it advisory instead of deleting the check.

## Limits
The runner uses import statements and line regexes. It misses dynamic imports, re-exports through aliases, and generated code; JS/TS import parsing is regex-based and Python uses the AST. Globs use `fnmatch` where `*` crosses `/`. It enforces structure, not correctness.
