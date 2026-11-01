# benchmarks: measuring skills with git history

Idea: git history holds **real answers**. A commit that was reverted or patched soon after is evidence that the decision was short-sighted. We show an AI the diff **as it was at the time** and ask "would you flag this?", with and without the skills.

## Pipeline
```
# 1. Mine cases from a real repo (needs at least a few hundred commits)
python git-history-miner/miner.py <git_repo> --out cases

# 2. Generate prompts: baseline and with skills
python runner/prepare_prompts.py --cases cases --out runner/out/baseline
python runner/prepare_prompts.py --cases cases --out runner/out/with_skill \
   --skill ../coding/line-durability/SKILL.md --skill ../core/myopia-patterns/SKILL.md

# 2b. Review the labels by hand (never with the AI under test)
python git-history-miner/review_labels.py --cases cases --list
python git-history-miner/review_labels.py --cases cases --show <case-id>
python git-history-miner/review_labels.py --cases cases --set <case-id>=valid|invalid|unclear

# 3. Have the AI answer each prompt and collect responses.json
#    (by hand, or: python runner/run_api.py --prompts runner/out/baseline --out runner/out/baseline/responses.json)

# 4. Score
python scoring/score.py --cases cases [--verified-only] \
   --results baseline=runner/out/baseline/responses.json \
   --results skill=runner/out/with_skill/responses.json
```

## Reading the result
- **recall**: share of truly short-sighted decisions that were caught.
- **false alarm rate**: share of good commits flagged by mistake. A skill that makes the AI flag everything is a bad skill.
- Keep a skill only if **F1 rises** and the **false alarm rate does not rise noticeably**.
- Cases whose answer is missing or errored are reported as `missing` and are NOT counted as "not flagged"; a run with missing cases is not comparable to a complete one.

- `score.py` always drops cases marked `invalid`; `--verified-only` keeps only cases a person marked `valid`.
- The miner ignores bot dependency bumps, lockfiles, CI files and docs, and does not treat lint/typo/docs fixes as evidence. These filters were added after a run on a real repo (qdrant/migration) showed such commits dominating the positives.

## Honest caveats
- The label "patched within N days" is an **estimate**: some fixes are unrelated, some bugs are not short-sightedness. Read 10-20 cases by hand to check the labels.
- You need enough cases (at least 30) to trust the numbers; fewer gives only an indication, and `score.py` says so.
- Leakage: prompts do not contain the fixing or reverting commit. If the repo is public the AI may have seen it in training; prefer your own private repos.
- Differences of a few cases between conditions are noise. With n cases per condition, a change of one decision moves recall by up to 1/n.
- `run_api.py` was not tested against the real API (no key was available); run 1-2 cases first.

## Judged A/B rounds
A second, cheaper benchmark compares an AI with and without the skills on fixed tasks, scored by a judge. Results, method and caveats: `RESULTS.md`. Judging kit and task sets: `judge/JUDGE.md`.
