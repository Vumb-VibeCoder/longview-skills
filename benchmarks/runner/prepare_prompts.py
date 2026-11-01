#!/usr/bin/env python3
"""Generate one prompt per case. Never reveals the label or the answer to the AI.

Usage:
  python prepare_prompts.py --cases ../cases --out out/baseline
  python prepare_prompts.py --cases ../cases --out out/with_skill --skill ../../coding/line-durability/SKILL.md --skill ../../core/myopia-patterns/SKILL.md
Each case -> <out>/<id>.md. Give the prompts to the AI (by hand or run_api.py) and collect JSON into responses.json.
"""
import argparse, glob, json, os, subprocess

TASK = """You are reviewing a change (diff) in a real project, AT THE TIME it was proposed.
Question: is this change likely to be reverted or patched within a few weeks because of a long-term
oversight (fragile assumption, symptom patching, tight coupling, swallowed errors, etc.)?

Answer with ONLY a single-line JSON object:
{"flag": true|false, "pattern": "M01..M11 or null", "reason": "<=2 sentences citing specific lines"}
Do not flag (flag=false) if the change is sound. Do not raise alarms indiscriminately."""


def git(repo, *args):
    return subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8", errors="replace").stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="../cases")
    ap.add_argument("--out", required=True)
    ap.add_argument("--skill", action="append", default=[])
    ap.add_argument("--max-diff-chars", type=int, default=12000)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    skill_text = ""
    for s in a.skill:
        skill_text += f"\n\n=== SKILL: {os.path.basename(os.path.dirname(s))} ===\n" + open(s, encoding="utf-8").read()
    n = 0
    for f in sorted(glob.glob(os.path.join(a.cases, "*.json"))):
        c = json.load(open(f, encoding="utf-8"))
        diff = git(c["repo"], "show", "--no-color", "--pretty=format:%s%n%n%b", c["commit"])[: a.max_diff_chars]
        parts = []
        if skill_text:
            parts.append("Apply the following skills while reviewing:" + skill_text)
        parts.append(TASK)
        parts.append(f"=== DIFF (commit {c['commit'][:8]}) ===\n{diff}")
        open(os.path.join(a.out, c["id"] + ".md"), "w", encoding="utf-8").write("\n\n".join(parts))
        n += 1
    print(f"Created {n} prompts in {a.out}")


if __name__ == "__main__":
    main()
