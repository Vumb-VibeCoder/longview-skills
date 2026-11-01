---
name: system-design-longevity
description: Review or produce a system design so it survives its expected lifetime - decide what must be stable (data model, public contracts, boundaries) versus what may stay disposable, size the design to the horizon class, and record one-way doors as ADRs. Use when designing or reviewing a service, data model, API, pipeline or architecture meant to last more than a few months.
metadata:
  domain: design
  status: READY
---
# System Design Longevity: stabilise the few things that are expensive to change

Most of a system is cheap to rewrite. A few things are not: stored data shapes, public contracts, identifiers, and the boundaries other teams build on. Spend design effort there and nowhere else.

## When to activate
Designing or reviewing a system, schema, API or pipeline. Run `horizon-fit` first. Class A/B: build the simplest thing and stop. Class C/D: continue.

## Procedure
1. **State the horizon, the dependents and the failure cost** from `horizon-fit`. They set how much of the steps below is warranted: class C needs steps 2-5; class D needs all.
2. **Inventory the one-way doors.** For each, classify with `reversibility-check`: stored data formats and identifiers, public API shapes and error contracts, event/message schemas, database choice for the system of record, authentication model, tenancy model, and anything customers integrate with. These get explicit design attention and an ADR (`adr-writer`).
3. **Draw the boundaries around change, not around nouns.** Use `change-vectors` to list what is most likely to change (pricing rules, providers, regulations, scale). Put each likely change behind a boundary so it touches one module. Keep things that always change together in the same module. If two modules would always be edited in the same commit, merge them or move the shared decision into one of them (`module-boundary-review`).
4. **Choose boring technology for the system of record.** Unproven components belong at the edges where they can be swapped. For each non-boring choice, write what is gained and the exit path if it fails.
5. **Make state explicit.** Name the single source of truth for every piece of data; derived copies must be rebuildable from it. Anything that cannot be rebuilt is a one-way door.
6. **Plan the evolution path for data and contracts:** versioned schemas, additive-only changes in public contracts, a migration approach that can run while the system is live, a deprecation process with an owner. If none of these exist the design is class A regardless of what the label says.
7. **Name the failure and scale modes** with `failure-and-scale-modes`, and the extension points that are genuinely needed with `extensibility-review`. Do not add flexibility without a named change that needs it (M10).
8. **Record the assumptions** about load, growth, users and team (`assumption-ledger`) with tripwires on the ones that would force a redesign (`assumption-tripwires`); apply `council-protocol` to any investment decision where builder, maintainer and minimalist disagree.
9. Finish with `verdict-format`.

## Mandatory questions
- Which decisions here could we not reverse in under a week?
- What is the single source of truth for each kind of data?
- What is the most likely requirement change, and how many modules does it touch?

## Output
The one-way-door list with ADR references, the boundaries and the change each protects against, the evolution path for data and contracts, the assumptions and tripwires, and the verdict.

## Exit path
- **Missing input:** no design or requirements: ask for them; do not review an idea that was never described.
- **Stop or hand off:** for a prototype (class A/B) list only the one thing that must not be thrown away, such as the data model.

## Limits
A design cannot be verified without running it; this review finds structural risk, not performance or correctness. It assumes the stated horizon; if the horizon changes, re-run it.
