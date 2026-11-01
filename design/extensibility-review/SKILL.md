---
name: extensibility-review
description: Decide where a design needs extension points and where it does not, by testing concrete anticipated changes against the structure and rejecting speculative flexibility. Use when asked "can we add X easily?", when reviewing plugin/config/abstraction layers, or when a design feels either rigid or over-built.
metadata:
  domain: design
  status: READY
---
# Extensibility Review: flexibility only where a real change needs it

Extensibility has a carrying cost: more code, more concepts, more places to be wrong. It pays only where a change will actually happen. Both rigid and over-built designs are failures.

## When to activate
A request to assess how easily a design accepts new features, providers, formats or customers; or a design containing abstraction layers, plugin systems, config flags or generic frameworks. Run `horizon-fit` first; class A/B gets no extension points.

## Procedure
1. **Collect concrete changes, not categories.** From `change-vectors` and from the people who own the roadmap, write 3-6 specific changes ("add a second payment provider", "support CSV and JSON export", "per-tenant limits"). Give each a likelihood in the horizon (HIGH / MEDIUM / LOW) and evidence for that likelihood (a ticket, a stated plan, a pattern of past requests). No evidence means LOW.
2. **Walk each change through the design.** List every file or module that must change, using `blast_radius.py` from `change-injection` when code exists. Record the count and whether any change requires a data migration or breaks a contract.
3. **Classify each change:**
   - CHEAP: touches one module and no contract.
   - STRUCTURAL: touches several modules or a contract; an extension point would reduce it.
   - ONE-WAY: needs a data or contract migration; apply `reversibility-check` now.
4. **Decide per change with this rule (first match wins):**
   - CHEAP: add nothing.
   - STRUCTURAL and likelihood HIGH: add the smallest seam that makes the second implementation easy (an interface at the point where two sides already exist). Use `council-protocol` if the cost is disputed.
   - STRUCTURAL and likelihood MEDIUM: do not build; add a tripwire ("when the second provider is requested, introduce the seam") and keep the code easy to refactor.
   - STRUCTURAL and likelihood LOW: add nothing and record the cost of doing it later.
   - ONE-WAY: design the contract or data format now to leave room (versioning, additive fields, opaque identifiers) even when the feature itself is deferred, because later is impossible or costly.
5. **Look for speculative flexibility already present:** abstractions with exactly one implementation and no planned second one, config options nobody sets, plugin frameworks with one plugin, generic types used for one case. Each is a candidate for removal if its carrying cost exceeds its benefit (`debt-ledger`).
6. **Check the opposite failure:** hard-coded values that appear in 3+ places and are likely to change (M01-style constants). These need one named source, not a framework.
7. **Verify, do not assert:** for the top change, outline or implement the change on a branch and measure the real radius. If the real radius is more than double the predicted one, the design understanding is wrong; correct it before deciding.

## Mandatory questions
- Which named change justifies this extension point, and what is the evidence it will happen?
- What does the extension point cost to carry each month?
- Is there any contract or data format that would be hard to extend later?

## Output
A table of change, likelihood with evidence, radius, class and decision; the list of speculative abstractions to remove; the contract-room decisions; the tripwires for deferred seams. For a verdict use `verdict-format` (Change tolerance carries the most weight).

## Exit path
- **Missing input:** no concrete future change given: ask for two or three likely ones; do not add extension points for imagined needs.
- **Stop or hand off:** if no anticipated change needs the extension point, recommend none.

## Limits
Likelihood estimates are judgments; the evidence column is what keeps them honest. Radius predictions from reading code can miss dynamic coupling (reflection, configuration, shared databases).
