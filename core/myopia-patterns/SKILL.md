---
name: myopia-patterns
description: Library of short-sightedness patterns (M01-M12) distilled from real reverted or repeatedly patched commits, including the over-engineering pattern M10. Use as a lookup when reviewing code, designs or logic to name the pattern, its signs and its smallest fix.
metadata:
  domain: core
  status: READY
---
# Myopia Patterns: a catalogue of familiar mistakes

A living catalogue. New patterns come from `benchmarks/` (commits that were reverted or patched again), never from imagination.

## How to use
For each finding, cite the pattern ID, the evidence (`file:line`), the concrete consequence, and the smallest fix. A finding without evidence is not a finding.

## Patterns
| ID | Pattern | Signs in code | Smallest fix | Do NOT flag when |
|---|---|---|---|---|
| M01 | Hard-coded values | magic numbers, URLs, paths, currencies embedded in logic | named config/constant | the value is a true constant (0, 1, 100 percent, HTTP 200) |
| M02 | Symptom patching | special-case `if` added instead of fixing the root condition | find the root condition, merge the branches | a documented, genuine exception exists in the domain |
| M03 | Swallowed errors | bare `except`, ignored return values, empty catch | catch the specific error, log, or let it surface | best-effort cleanup that is explicitly commented |
| M04 | Copy-paste | near-identical blocks in several places | extract once the **third** copy appears | two copies that may diverge (premature merge = M10) |
| M05 | Fixed-scale assumption | nested loops, load-everything-in-memory | measure, then pick the structure | bounded input proven by evidence |
| M06 | Order/time dependence | correct only if called in a given order or at a given time | make state explicit | the order is enforced by the type or the framework |
| M07 | Tight coupling | module A reads module B's internals | define an interface | both modules always change together by design |
| M08 | Do-everything function | one function, several boolean flags, many responsibilities | split by responsibility | a short orchestrator that only sequences calls |
| M09 | Unexplained decision | odd structure with no stated reason | ADR or a "why" comment | the reason is obvious from names and context |
| M10 | Premature abstraction (over-engineering) | interface/class/layer with a single implementation and no concrete second use | delete until a second implementation exists | a public API or plugin boundary with a stated external need |
| M11 | Extended present | model or parameter assumes today's value will persist | scenarios plus a value range | the value is fixed by law or physics |
| M12 | Imprecise money | prices, totals, tax or balances computed with binary floats | `Decimal` or integer minor units, one rounding rule | a display-only estimate that is never stored, summed or compared |

M10 is the over-engineering pattern; it matters as much as the short-sighted ones. A review that only finds under-engineering is biased.

## Admission rule for new patterns
A pattern is added only when at least 2 cases in `benchmarks/cases/` confirm it, and it must carry a "Do NOT flag when" entry.

## Exit path
- **Missing input:** no case to match: do not apply patterns by name alone.
- **Stop or hand off:** if nothing matches, say `no pattern matched`; do not stretch a pattern to fit.

## Limits
Patterns are lenses, not verdicts. A match without evidence of consequence is a question to ask, not a defect to report.
