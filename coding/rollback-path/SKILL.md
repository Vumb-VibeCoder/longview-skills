---
name: rollback-path
description: Make sure every code or system change ships with a tested way back before it starts - restore point, kill switch, expand-then-contract schema changes, backups before destructive steps, and a stated trigger for going back. Use when writing, deploying, migrating, deleting data, changing a schema or public API, or building a system in stages. Ships a rollback plan template.
metadata:
  domain: coding
  status: READY
---
# Rollback Path: never make a change you cannot take back

A change that turns out wrong is normal. A change that cannot be undone is the real problem. This skill asks for the way back first and the change second.

## When to activate
Any change to code, data, configuration or infrastructure that will run somewhere other than a scratch folder. It applies from class B upward (`horizon-fit`); for class A a plain `git` commit is enough. It always applies to data deletion, schema changes, migrations, public API changes and deploys. Pair it with `reversibility-check` when the decision itself is hard to undo.

## Required inputs
What is changing, where it runs, what state it touches (files, database, external services), and who or what depends on it. If you cannot say what state it touches, stop and find out before writing anything.

## Procedure
1. **Name the restore point first.** A commit hash or tag, a branch, a database backup or snapshot, a copy of the config. Write down exactly how to get back to it.
2. **Cut the change into small steps.** Each step is shippable and checkable on its own, and a failure in step N never needs step N+1 to repair it.
3. **Pick the way back for each step** from the table below. Prefer the cheapest mechanism that fully works.
4. **Back up before anything destructive.** Deleting files or rows, dropping a column, overwriting data: take a copy, check the copy can be read, only then proceed. A backup that was never restored is a guess.
5. **Keep the old path alive until the new one is proven.** Run both, switch by flag, and remove the old code in a later, separate change.
6. **State the trigger and the deadline.** Which observation means "go back" (error rate, failed check, wrong output), and how long you watch before calling it good.
7. **Rehearse once when the cost of failure is high** (money, user data, security). Run the rollback on a copy and record that it worked.
8. **Record the plan** using `templates/rollback-plan.example.md`. For a decision that is hard to reverse, also write an ADR (`adr-writer`).

## Ways back by change type
| Change | Way back | Watch out for |
|---|---|---|
| Code edit | small commits, `git revert`, tag before merge | reverting a commit that others already built on |
| New behaviour | feature flag or config switch, default off | flag left on for years; remove it after the soak period |
| Schema change | expand, migrate, contract: add new column first, copy data, switch reads, drop old column last | a `down` migration that loses data is not a rollback |
| Data migration or bulk edit | snapshot first, keep the source until verified, make the script idempotent | scripts that cannot be rerun after a partial failure |
| Deleting data or files | move to a trash folder or soft-delete first, purge later | purge jobs that run before anyone notices |
| Public API or contract | add the new version beside the old, deprecate with a date | removing a field callers still send |
| Dependency or vendor swap | wrap it behind one adapter, keep the old one installed until the switch holds | data formats that only the new vendor can read |
| Deploy | previous artifact kept, one-step redeploy, health check gating | a rollback that needs the same database state the new version already changed |
| Infrastructure or config | version-controlled config, plan before apply, snapshot of the running state | drift between what is in git and what is live |

## Mandatory questions
- What exact command or step returns the system to the state before the change?
- Has that way back been run, or only written down?
- What data does the change write that the old version cannot read?
- What is the point after which going back is no longer possible, and have we said so out loud?
- Who or what notices that it went wrong, and how fast?

## Output
A rollback plan with five lines per step: **change**, **restore point**, **way back**, **trigger**, **point of no return** (or `none`). Use the template. If any step has no way back, say `ONE-WAY: <step>` and stop for approval; do not continue silently.

## Exit path
- **Missing input:** you cannot say what state the change touches: ask, or limit the work to read-only steps until it is known.
- **No way back exists:** mark `ONE-WAY: <step>`, propose the nearest reversible alternative (soft delete, expand-contract, flag), and wait for an explicit yes before going on.
- **Stop or hand off:** if the way back fails during a rollback rehearsal, stop the change, fix the rollback, and rehearse again. For decisions that are costly to undo, hand over to `reversibility-check`.

## Limits
This skill cannot make a physically irreversible action reversible (sending an email, a payment, a published secret). It can only ask for a safer order of steps and an explicit approval. It does not test your backups; it asks whether someone did. Rollback of a deploy that already changed shared data may need a manual fix that no script can cover.
