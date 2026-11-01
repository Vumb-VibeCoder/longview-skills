---
name: council-protocol
description: Structured three-role debate (Builder, Future Maintainer, Minimalist) over a significant design or architecture decision, with an explicit investment formula, to prevent both short-sighted and over-engineered choices. Use for non-trivial class C/D decisions, especially hard-to-reverse ones, and whenever a reviewer is torn between "do more" and "do less".
metadata:
  domain: core
  status: READY
---
# Council Protocol: three roles, one decision

Counters short-sightedness **and** over-engineering through structured argument, ending in a rule-based decision.

## When to activate
Class C/D decisions that are non-trivial. Skip for cheap two-way-door decisions (see `reversibility-check`): just decide. Class A/B with no escalator: skip.

## Roles
- **Builder:** proposes the solution and says which change vectors it prepares for.
- **Future Maintainer:** someone who must change this in 12 months with no context. Attacks: hard to understand, hard to change, hidden assumptions, missing tests.
- **Minimalist (YAGNI):** attacks everything superfluous. Each layer, parameter, abstraction must prove it is needed. Names what can be cut.

## Procedure
1. **Builder** states the proposal in at most 10 lines, including the change vectors addressed (`change-vectors`) and the assumptions it relies on (`assumption-ledger`). Also states the **minimal baseline** (the simplest thing that works now) so the Minimalist has something concrete to compare.
2. **Maintainer:** at most 3 strongest objections, each with a concrete scenario or number.
3. **Minimalist:** at most 3 strongest objections, each naming exactly what to cut and the evidence that it is unneeded.
4. **Builder** answers every objection: ACCEPT, REBUT with evidence, or AMEND the proposal.
5. **Decide each flexibility investment with this rule.** Invest now only if

   `P(change within the horizon) x (C_late - C_prepared) > C_prep + C_carry`

   - `C_late`: cost of making that change later with no preparation
   - `C_prepared`: cost of making it later if the preparation already exists
   - `C_prep`: cost of building the preparation now
   - `C_carry`: ongoing cost of the added complexity over the horizon (reading, testing, maintenance)
   Use ranges, not point values. If the inequality flips inside the ranges, **defer and set a tripwire** (`assumption-tripwires`), unless the decision is a one-way door: then apply `reversibility-check` and decide on exit cost.
6. **Record** the outcome as ACCEPTED / REJECTED / DEFERRED (with the tripwire that reopens it). Non-trivial accepted decisions get an ADR (`adr-writer`).
7. **Tie-break:** if the roles cannot agree, choose the more reversible option.

## Rules
- Every objection needs a scenario or a number. "It feels complex" is not an objection.
- No role may be skipped. If a role finds nothing, write "none found" with the reason it looked.
- An objection answered with "defer" must produce a tripwire, not a promise.

## Output
```
Proposal (<=10 lines) | Baseline
| Objection | Role | Response (ACCEPT/REBUT/AMEND) | Reason + evidence |
Investment checks: option | P | C_late - C_prepared | C_prep + C_carry | decision
DECISION: ACCEPTED | REJECTED | DEFERRED | Reopen when: <tripwire>
```

## Limits
When one AI plays all three roles it can converge falsely. For one-way doors, have a **separate session or a human** play the adversarial roles. The formula is only as good as its estimates: show the ranges.
