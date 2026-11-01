---
name: adr-writer
description: Write Architecture Decision Records that capture why a significant decision was made, the alternatives rejected, accepted costs and the conditions to revisit it, then lint them. Use for one-way or costly decisions in class C/D work, after a council-protocol outcome, or when code contains a strange structure nobody can explain. Ships a template and an ADR linter.
metadata:
  domain: coding
  status: READY
---
# ADR Writer: record the why, not just the what

Code shows what was built; an ADR preserves **why**, what was rejected, and when to reconsider. It is the antidote to M09 (unexplained decision). It is also easy to overdo: an ADR for every trivial choice is noise (M10 in documentation form).

## When to write an ADR
Write one when ALL of: the work is class C/D (`horizon-fit`), AND at least one holds:
- the door is COSTLY or ONE-WAY (`reversibility-check`)
- `council-protocol` produced an ACCEPTED or DEFERRED decision
- the decision constrains other teams or modules (a boundary, a public interface)
- a future maintainer would reasonably "fix" the result without knowing why it is so

Do **not** write one for CHEAP two-way decisions, style choices, or anything a code comment explains in one line.

## Procedure
1. **Gather evidence first** (cite it): code locations, measurements, ledger assumption ids, the council record, incidents.
2. **One decision per ADR.** If you need "and", write two.
3. Copy `templates/adr.template.md`, name the file `NNNN-kebab-slug.md` (next number; never reuse or renumber), and fill every section:
   - **Context:** the forces and facts, not the solution
   - **Decision:** active voice ("We will ...")
   - **Alternatives considered:** at least two, always including *do nothing / minimal baseline*, each with the reason it lost
   - **Consequences:** positive, negative and **accepted** costs, and risks taken on knowingly
   - **Revisit when:** observable conditions, referencing tripwire ids (`assumption-tripwires`)
   - **Related:** assumption ids, fitness rule ids (`fitness-functions`), debt ids (`debt-ledger`), and `Supersedes:`
4. **Status lifecycle:** Proposed -> Accepted or Rejected; later Deprecated or `Superseded by ADR-NNNN`. Never edit an accepted ADR's decision. To change it, write a new ADR that lists the old one under `Supersedes:`, and set the old one's status to `Superseded by ...`. Typos and added links are fine.
5. **Write rejected decisions too**: a Rejected ADR stops the same proposal being re-argued.
6. **Lint:** `python scripts/adr_lint.py <adr_dir>`. It checks filename and numbering, status, date, required sections non-empty, at least two alternatives, supersede links in both directions, a concrete "Revisit when" for ONE-WAY doors, and leftover placeholders in Accepted ADRs. Exit 1 on any problem.
7. If the ADR implies a mechanical rule, create it with `fitness-functions`; if it implies a risky assumption, add it to `assumption-ledger`.

## Mandatory questions
- Would a stranger understand, in two minutes, why we did not choose the obvious alternative?
- Is every "Revisit when" something that can actually be observed?
- Does the ADR state what we gave up, not only what we gained?

## Output
The ADR file(s), the lint result, and a one-line index entry (`ADR-NNNN | title | status`).

## Limits
Cannot recover reasoning nobody recorded: when reconstructing an old decision, mark Context as "reconstructed from code and history" and list what is unknown. The linter checks structure, not whether the reasoning is sound.
