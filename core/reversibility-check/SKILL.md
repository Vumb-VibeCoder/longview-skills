---
name: reversibility-check
description: Classify decisions as cheap-to-reverse or one-way doors and estimate the cost of undoing them. Use when choosing a technology, schema, stored data format, public API, contract, vendor or any hard-to-change option, before committing.
metadata:
  domain: core
  status: READY
---
# Reversibility Check: how expensive is it to be wrong?

Decide fast where retreat is cheap; decide slowly and write it down where it is not.

## Classification (by cost of undoing after 6 months of use)
| Door | Undo cost | Examples | Handling |
|---|---|---|---|
| CHEAP (two-way) | up to ~2 days, no data loss, no outside party affected | rename a function, swap an internal helper, feature behind a flag | decide fast, no ceremony |
| COSTLY | days to weeks; needs a migration; internal impact only | change an internal data model, replace a framework | decide with `council-protocol`; record the reason |
| ONE-WAY | data loss, external commitments, or an effective rewrite | stored data format, public API, schema others rely on, contract, vendor lock-in, locking up capital | decide slowly; ADR required |

## Procedure
1. List the decisions inside the change (including implicit ones: a field name in stored data is a decision).
2. For each, estimate the **exit cost at 6 months**: person-days, data lost, outside parties affected, reputation.
3. Classify with the table. When unsure between two classes, take the more severe.
4. **COSTLY and ONE-WAY** need: the reason, the alternatives rejected, and a condition for revisiting. Record with `adr-writer`.
5. **Try to convert a one-way door into a cheaper one**: versioning, an adapter at a seam, dual-writing, storing the raw source alongside derived data, a feature flag, a pilot. Do it only if `cost of the hedge < P(regret) x exit cost` (same logic as `council-protocol`). Otherwise accept the door and say so.
6. Feed the result into `verdict-format` (Reversibility dimension).

## Mandatory questions
- If this is wrong, what do we lose besides time: data, trust, money, a contract?
- Can we run it small first (pilot, shadow mode) before committing the whole thing?

## Output
| Decision | Exit cost at 6 months | Door | Hedge available (cost) | Hedge worth it? | ADR |

## Limits
Not every door deserves a hedge. Turning every one-way door into a two-way one is over-engineering (M10): `horizon-fit` sets how much to spend.
