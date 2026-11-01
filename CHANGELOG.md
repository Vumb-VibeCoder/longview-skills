# Changelog

Versions follow the skill bundle, not Python packaging. Benchmark numbers are in `benchmarks/RESULTS.md`.

## v3.14
- `long-horizon-cashflow`: reverse-stress thresholds are rounded safely and re-run at the printed value.
- `verdict-format`: INSUFFICIENT EVIDENCE gains a `Fix now` line for known control gaps.
- `horizon-fit`: secrets go in environment variables even in class B.
- README rewritten with badges; repo health files added (issue and PR templates, security, conduct, changelog).

## v3.13
- `horizon-fit`: class split when only some components are sensitive; one-user scripts with no end date stay class B.
- Line numbers in `file:line` count from the first line of the code given.
- Round 4 benchmark results added (Haiku 5.5 medium, two runs; Sonnet 5.5 low, one run).

## v3.2
- Patch for round 3: skills named in ROUTE must be applied, unstated assumptions must be named, unrun code must say `Not run.`

## v3.1
- Added `core/skill-router`, the mandatory ROUTE and CLASS header, the TEMPORARY IS ENOUGH block and the INSUFFICIENT EVIDENCE shape.

## v3
- English rewrite, unified ledger schema, tested scripts, validator, CI, benchmark harness.
