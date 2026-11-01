# longview-skills

Skills that make an AI **avoid short-sightedness**: judging whether a line, a module, a whole codebase, a financial plan, a design or a UI will hold up over its real lifetime, and knowing when long-term thinking is **not** needed.

## What makes it different
| Idea | Where |
|---|---|
| Benchmark from git history (real answers) | `benchmarks/` |
| Inject changes, measure blast radius | `coding/change-injection/` |
| Assumptions with tripwires and expiry | `core/assumption-tripwires/` |
| Three-role council against both short-sightedness and over-engineering | `core/council-protocol/` |
| Technical debt with principal, interest and breakeven | `coding/debt-ledger/` |
| Evidence-scored verdicts with a fixed decision rule | `core/verdict-format/` |
| Router: right skills per request, mandatory ROUTE/CLASS header, regression-tested | `core/skill-router/` |

## See it work
`EXAMPLE.md` walks one real function through the skills, with real script output and the verdict arithmetic.

## Layout
`core/` (11 skills, every domain; `skill-router` runs first) - `coding/` (11) - `finance/` (5) - `design/` (3) - `ui/` (4). Each skill is a folder with `SKILL.md`, and optional `scripts/` and `templates/`. `dist/` holds one upload-ready zip per skill.

## Install
- **claude.ai:** upload each zip from `dist/` at Settings > Capabilities > Skills.
- **Claude Code:** copy the skill folders into `.claude/skills/`.

## Use
1. Give the AI `AGENTS.md` at the start of a session (or put it in the project's instruction file).
2. Ask when needed: "Apply `coding/line-durability` to this file."
3. Run the measuring scripts (Python 3.10+, standard library only). Every script lives inside its skill:
```
python coding/line-durability/scripts/scan_line_risks.py path/to/code
python core/assumption-tripwires/scripts/tripwire_check.py core/assumption-tripwires/templates/assumptions.example.json
python coding/debt-ledger/scripts/debt_calc.py --help
python finance/long-horizon-cashflow/scripts/cashflow.py finance/long-horizon-cashflow/templates/model.example.json
python core/skill-router/scripts/route.py --test
python core/skill-router/scripts/route.py "your request text"
python benchmarks/git-history-miner/miner.py path/to/git/repo --out benchmarks/cases
```
4. Check the repo after any edit: `python tools/validate_repo.py` (add `--build` to rebuild `dist/`).
5. Measure whether the skills help with `benchmarks/` (see `benchmarks/README.md`). Judged A/B results so far: `benchmarks/RESULTS.md` (indicator only, not proof).

## Status
See `STATUS.md`. READY means: English text, internally consistent procedure, bundled scripts executed on test inputs. It does **not** yet mean benchmark-proven; no benchmark results exist so far.

## Warning
The finance skills are risk-analysis frameworks, **not investment, tax or legal advice**.
