---
name: change-injection
description: Measure how flexible a codebase really is by implementing realistic change scenarios (new currency, data x100, storage swap, new input, external API change, new entity type) on a throwaway branch and counting what had to change. Use before finalising a design, when judging Change tolerance, or when someone asks how many places a change would touch. Ships a git-based blast-radius script.
metadata:
  domain: coding
  status: READY
---
# Change Injection: turn "is it flexible?" into a number

Opinions about flexibility are cheap. This skill makes the change and counts.

## When to activate
Class C/D code that can be run or at least edited (run `horizon-fit` first). Use before locking a design or when feeding the Change tolerance dimension of `verdict-format`.

## Safety rules
Work only in a **throwaway branch or git worktree**, never on the main branch or the user's working directory:
`git worktree add ../inject-1 -b inject/1`. Never push, never commit to the real branch, and delete the worktree when done (`git worktree remove ../inject-1`). If the repo cannot be modified or run, say so and fall back to a **desk estimate**, labelled as such and not as a measurement.

## Procedure
1. **Pick 3-5 scenarios** from `change-vectors` (the most likely ones), not from convenience. Add one **control** scenario that should be trivial (for example, rename a user-visible label); if the control is not trivial, the codebase has a deeper problem.
2. **Implement the minimal change** that makes each scenario actually work in its own worktree: not a sketch. Include updating tests that the change legitimately breaks.
3. **Measure each scenario:** `python scripts/blast_radius.py <worktree> --src <src_dir>`. It reports edited existing files, **modules edited (the radius)**, source lines, and separately new files, test files and ignored noise (lockfiles, snapshots, generated). Add: tests that broke and how many modules had to "know" about the change.
4. **Read the radius** (modules edited per scenario). Judge it against the scenario's nature: adding a new entity type touching 1 module plus new files is healthy; touching 6 modules is tight coupling (M07, see `module-boundary-review`). Many `if/elif` edits for a new type points to M02/M08.
5. **Score Change tolerance for `verdict-format`:** per scenario 1 module = 3, 2 = 2, 3-4 = 1, 5+ = 0; use the **median** across non-control scenarios and also report the worst case. This table is the evidence.
6. Clean up the worktrees. Keep a branch only if the change is certain to happen.

## Scenario library
| Scenario | What it reveals |
|---|---|
| Multi-currency / language / time zone | whether single-value assumptions are spread (M01, M11) |
| Data x100 | which structures or queries break or slow sharply (M05) |
| Storage swap (file to DB, DB to DB) | whether logic is entangled with persistence |
| New platform or input channel | single entry point versus logic scattered |
| Change of an external API | number of direct call sites (no seam) |
| New entity type | count of `if/elif` branches to edit |

## Output
| Scenario | Existing files edited | Source lines | Tests broken | Radius (modules) | Score | Notes |
Then the median score, the worst case, and the evidence path to give `verdict-format`.

## Limits
Changes made by an AI may differ from how the team would do them. Use results as a relative indicator across parts of the system, not an absolute number. Scenarios that need real infrastructure (production data volumes) can only be desk-estimated: say so.
