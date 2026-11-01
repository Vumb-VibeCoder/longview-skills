# Longview Skills: Judge Kit

## How to run (A/B test)
1. Open two fresh sessions of the AI under test. Do not tell it about the judging.
2. Session A (baseline): give it the task only.
3. Session B (with skill): load `longview-skills` (AGENTS.md + skills), then give the same task.
4. Paste the tasks one at a time. Send each answer back to the judge (Claude) in the format:
   `TASK <n> | A: <answer> | B: <answer>`
5. Judge scores A and B blind (labels shuffled) using the rubric below.

Do not show the AI the "Expected" column.

## Tasks (hidden expectations)

| # | Task for the AI | Expected behaviour (judge only) |
|---|---|---|
| T1 | "Write a script that renames 20 files in a folder once." | Class A/B. TEMPORARY IS ENOUGH. No framework, no config layer, no tests suite. Correct and brief. Penalise over-engineering (M10). |
| T2 | "Write a function that totals an order. Tax is 10%, prices in USD. It will be used by our live shop for years." | Class C/D, money escalator. Flags hard-coded tax/currency (M01), float money, lists assumptions with expiry. Cites evidence. Verdict in the standard shape. |
| T3 | Give a 15-line function with `except: pass` and a magic URL. "Review for long-term risk." | Names M03 and M01 with `file:line`. Does NOT flag trivial constants (0, 1, 200). Smallest fix per finding. |
| T4 | "Should I add a plugin system now? One user, internal tool, 2 months old." | Rejects or defers. Uses the investment formula or reasoning equivalent, gives a tripwire to reopen. Not a flat yes. |
| T5 | "Review this design" with no code, no context, three dimensions unknowable. | INSUFFICIENT EVIDENCE. Lists exactly what to gather. Must NOT output REWRITE/KEEP. |
| T6 | "Can my savings of X last 30 years? Inflation 3%, return 5%." (give numbers) | Runs the scenarios (shocks, first negative month) instead of one average path. Runs or simulates `cashflow.py` honestly. Says what is not measured. States limits. |

## Rubric (per task, 0-2 each, max 12)
| Criterion | 0 | 1 | 2 |
|---|---|---|---|
| Fit: right depth for the horizon (class) | wrong class or wrong depth | right class, depth uneven | right class and proportional depth |
| Evidence: claims cite `file:line`, a number or a named assumption | none | some | every conclusion |
| Format: follows the skill's exact output shape and vocabulary | ignored | partial | exact |
| Honesty: states limits, never claims a measurement it did not run | fabricates | vague | explicit about unmeasured parts |
| Decision: verdict follows the decision rule (e.g. score total, escalators) | contradicts rule | roughly right | rule applied correctly |
| Economy: no padding, no needless ceremony for small tasks | heavy padding | some | lean |

## Scoring
- Sum per task, then total over 6 tasks (max 72).
- Skill effect = total(B) - total(A). Per-task effect shown too.
- Reading the result:
  - B - A >= +10: skill clearly helps.
  - +4 to +9: helps, check which tasks.
  - -3 to +3: no demonstrated benefit.
  - Below -3: skill hurts (usually over-engineering on T1/T4).
- With only 6 tasks the result is an indicator, not proof. Repeat each task 3 times and average to reduce noise.

## Hard-fail flags (note them separately)
- F1: T1 answered with architecture or layers (over-engineering).
- F2: T5 gives REWRITE/KEEP without evidence.
- F3: any answer claims it ran a script it did not run.
- F4: B ignores AGENTS.md step 1 (no class stated) on T2-T6.

## Judge output format
```
TASK n: A=<score>/12  B=<score>/12  | key difference: <one line>
Flags: <F1-F4 or none>
TOTAL: A=<>/72 B=<>/72  Effect=<+/->  Reading: <...>
```

## Hold-out task set (round 3, unseen by the skill authors)
| # | Task | Expected behaviour (judge only) |
|---|---|---|
| S1 | One-off script converting a 300-row CSV to JSON, deleted afterwards | Class A, Do/Safeguard/Debt/Re-class block, at most one safeguard |
| S2 | Signup function that stores passwords, runs for years | Class C (security), slow salted hash, unique email, assumptions, "Not run" |
| S3 | 12 microservices share one database, every release breaks something; rewrite? | INSUFFICIENT EVIDENCE with exact missing inputs; no KEEP/REWRITE guess |
| S4 | Pay off a 6.5% loan or invest $20,000 | Regret/sensitivity trace (matrix or break-even), conditions, not advice |
| S5 | Rename prop `variant` to `kind` on a Button | Breaking vs safe, deprecation path, both branches (internal vs published), props_diff not run stated |
| S6 | Postgres or a document store for 10 years of orders | Class D, one-way door, conditions that flip the choice, ADR |

## Rules learned in rounds 1-2
- Open a fresh chat for every task; shared chats leaked earlier answers into later ones.
- Judge the with-skill answer for visible traces of every skill it names.
- Verify numbers and script claims by running them before scoring honesty.

## Round 4 (hard set for small models)
See `ROUND4_PROMPTS.md` (paste-only) and `ROUND4_JUDGE.md` (hidden expectations, ground truth for H3). Written after round 3 and not used to tune the skills.
