# Contributing

Thanks for taking a look. A few ground rules keep the repo consistent.

## Before you open a pull request

1. Run `python tools/validate_repo.py` and `python tests/test_regression.py`. Both must pass.
2. If you changed a skill, a script or a template, run `python tools/validate_repo.py --build` and commit the updated `dist/` zips. CI fails on stale zips.
3. If a script name appears in more than one skill (for example `cashflow.py`), update every copy. The validator checks they are identical.

## Conventions

- Everything is in English, including comments and examples.
- Scripts use the Python standard library only and must run on Python 3.10+.
- Scripts exit `0` for success, `1` for a finding or failed check, `2` for bad input. Don't let bad input end in a traceback.
- Open files with an explicit `encoding="utf-8"`.
- Every `SKILL.md` needs `name` and `description` frontmatter, an `## Exit path` section (see `templates/SKILL.template.md`), and the skill has to appear in the routing table in `core/skill-router/SKILL.md`.
- A new script needs at least one test in `tests/test_regression.py`.

## Claims

If you say a skill works, point to a measurement or a script run. "Seems better" is fine in a discussion, but it doesn't belong in a `SKILL.md`.

## Conduct and security

Be civil (see `CODE_OF_CONDUCT.md`). Report security problems as described in `SECURITY.md`.
