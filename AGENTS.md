# AGENTS.md: mandatory process for AI

This repo teaches AI to think long-term **with evidence**. Read this file first, every session.

## Principles
1. No gut-feel judgments. Every conclusion carries **evidence** (code `file:line`, a measurement, a named assumption).
2. Long-term is not always right. Always run `horizon-fit` first. If it returns TEMPORARY IS ENOUGH, do not over-design.
3. Missing input: **ask or stop**. Never guess silently.
4. State limits: say what the skill cannot conclude.
5. Never claim a measurement you did not run. A script that was not executed is "not measured".

## First lines of every answer (mandatory)
Before any content, print exactly these two lines (see `core/skill-router`):
```
ROUTE: <skills used in order> | skipped: <skill: reason>
CLASS: <A|B|C|D> [PROVISIONAL] | Components escalated: <none | list>
```
List only skills whose output you actually used in the answer; a skill you name but did not apply counts as a routing error. If a chosen skill ships a script that you did not run, write `NOT MEASURED: <script>` in the answer. An answer without these lines counts as not routed. Pick skills with the routing table in `core/skill-router/SKILL.md`: at most 4 beyond `horizon-fit` and `verdict-format`, each tied to a risk named in the CLASS reason. Money, data, security, legal or safety questions always route to the matching `finance/` or `coding/` skills. A review request with no artifact to review gets `VERDICT: INSUFFICIENT EVIDENCE` and a list of needed inputs, never a guessed risk list.

## Process (the maximum, not the default)
The router picks the subset for this request. Running every step on a small request is a routing error.
```
0. skill-router          pick the skills; print ROUTE and CLASS lines
1. horizon-fit            class A-D; escalators; TEMPORARY IS ENOUGH or continue
2. assumption-ledger      list assumptions
   assumption-tripwires   attach an automated check + expiry to each risky assumption
3. domain skills          coding/ finance/ design/ ui/   (line -> module -> system -> logic)
4. change-injection       measure blast radius with real changes (code only)
5. council-protocol       Builder vs Maintainer vs Minimalist
6. three-horizon-map      verdict now / 1 year / 5 years
7. verdict-format         scores + evidence + KEEP | REINFORCE | REWRITE | TEMPORARY IS ENOUGH | INSUFFICIENT EVIDENCE
8. debt-ledger            record debt with interest; adr-writer records the reason
9. calibration-loop       store predictions to compare with reality later
```
**Exit path:** if step 1 returns TEMPORARY IS ENOUGH (class A/B, no escalator), do only: make it correct, record its debt, record the re-class trigger. Stop. Print the four-line block from `horizon-fit` (Do / Safeguard / Debt / Re-class trigger). At most one safeguard beyond correctness (for example a dry run for a destructive action), and it must name the failure cost it prevents. If only some components are escalated (money, data, security, users), run the full process for those components only.

## Skill status
- `READY`: complete, English, procedures checked for internal consistency; scripts (where present) were executed on test inputs.
- `PLANNED`: skeleton only; use as a hint, not as a rule. (No skill is PLANNED at the moment.)

If the answer changes with a fact the user did not give (for example internal use versus a published library), answer both branches in two lines and name the fact; do not assume one. Any code you wrote and did not execute carries the line `Not run.`

Never claim a run that did not happen: if no shell exists, write `NOT MEASURED: <what>` and give a hand-computable bound.

Every skill follows `templates/SKILL.template.md`. Shared vocabulary: classes A-D (`horizon-fit`), six scored dimensions and verdict names (`verdict-format`), pattern IDs M01-M11 (`myopia-patterns`).
