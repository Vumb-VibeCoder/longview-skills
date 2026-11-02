# longview-skills

![CI](https://github.com/Vumb-VibeCoder/longview-skills/actions/workflows/ci.yml/badge.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Skills: 37](https://img.shields.io/badge/skills-40-8A2BE2)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)
![Works with: Claude Code, claude.ai, AGENTS.md](https://img.shields.io/badge/works%20with-Claude%20Code%20%7C%20claude.ai%20%7C%20AGENTS.md-D97757)

40 skills that make an AI assistant ask two questions before it touches your code, design or budget: will this still hold up in a few years, and does it need to?

Assistants tend to fail in one of two directions. They patch the quick way, or they build a platform nobody asked for. These skills try to stop both. A throwaway script stays a throwaway script. A billing module that will outlive three teams gets real review. The same method also covers system design, UI and personal or business money.

## What's inside

| Idea | Where |
|---|---|
| Decide how long a thing needs to live before judging it | `core/horizon-fit` |
| Pick which skills apply, and which to skip | `core/skill-router` |
| One verdict format with scores, evidence and a fixed decision rule | `core/verdict-format` |
| Track assumptions with owners, expiry dates and tripwires | `core/assumption-tripwires` |
| Review from three angles: builder, maintainer, minimalist | `core/council-protocol` |
| Technical debt as principal, interest and break-even | `coding/debt-ledger` |
| Secrets, untrusted input, least privilege, data kept | `coding/security-durability` |
| Tests that stay trustworthy for years: no rot, no flakiness | `coding/test-durability` |
| A way back for every change: restore point, kill switch, backups | `coding/rollback-path` |
| Inject a change and measure how far it spreads | `coding/change-injection` |
| Review one change: size, tests, intent, way back | `coding/diff-review` |
| Catch what AI-written code gets wrong: invented packages, stubs, tests that cannot fail | `coding/ai-code-audit` |
| Will this API, schema or flag change break its consumers? | `coding/api-contract-stability` |
| Mine a repo's git history for real "this got patched or reverted" cases | `benchmarks/` |

Skills live in five folders: `core/` (11), `coding/` (17), `finance/` (5), `design/` (3) and `ui/` (4). Each one is a folder with a `SKILL.md` and, where something can be measured, a `scripts/` and `templates/` folder.

`EXAMPLE.md` walks a single function through the whole process with real script output.

## Install

**Claude Code:** copy the skill folders you want into `.claude/skills/`.

**claude.ai:** upload the zips from `dist/` under Settings > Capabilities > Skills. There is one zip per skill.

For other assistants, put `AGENTS.md` in the project's instruction file and point the assistant at the skill folders.

## Usage

1. Give the assistant `AGENTS.md` at the start of a session.
2. Ask for a skill by name, for example "apply `coding/line-durability` to this file".
3. Run the scripts directly if you want the numbers. They need Python 3.10+ and nothing else.

```sh
python coding/line-durability/scripts/scan_line_risks.py path/to/code
python coding/debt-ledger/scripts/debt_calc.py --ledger coding/debt-ledger/templates/debt.example.json
python finance/long-horizon-cashflow/scripts/cashflow.py finance/long-horizon-cashflow/templates/model.example.json
python core/skill-router/scripts/route.py "should I rewrite this module?"
python coding/ai-code-audit/scripts/scan_ai_risks.py path/to/code
python coding/diff-review/scripts/diff_stats.py my-change.diff     # or: --git main...feature
python coding/api-contract-stability/scripts/contract_diff.py old.json new.json
python benchmarks/git-history-miner/miner.py path/to/git/repo --out benchmarks/cases
```

Exit codes are consistent for the finance scripts: `0` means fine, `1` means a scenario marked `must_survive` failed, and `2` means the input was bad (unreadable file, missing field, unknown key).

## Development

```sh
python tools/validate_repo.py           # structure, routing table, duplicate scripts, dist/ freshness
python tools/validate_repo.py --build   # same checks, then rebuild dist/
python tests/test_regression.py         # script behaviour
```

CI runs both on every push and pull request. See `CONTRIBUTING.md` before sending a change. If an assistant with these skills answers badly, please open a "wrong answer" issue: those become new benchmark tasks. Other files: `CHANGELOG.md`, `SECURITY.md`, `CODE_OF_CONDUCT.md`.

## Status

This is a working draft. I have read every skill for consistency and run every script on sample input. The effect on real assistant output is measured only lightly: `benchmarks/RESULTS.md` has four A/B rounds, six tasks each, one judge, run on Haiku 5.5 and (once) Sonnet 5.5. With the skills, the judged score was higher in every run, by 16 to 31 points out of 72. The judge also wrote the tasks and the rubric, and several skills were patched after seeing the tasks, so read those numbers as a hint, not as proof.

The router's built-in test cases were written after its early failures, so passing them says little about new requests. `STATUS.md` lists the known gaps.

The router matches English keywords only. Requests in other languages may fall back to `horizon-fit`.

## Disclaimer

The finance skills are frameworks for thinking about risk. They are not investment, tax or legal advice.

## License

MIT. See `LICENSE`.
