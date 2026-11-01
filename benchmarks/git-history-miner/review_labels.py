#!/usr/bin/env python3
"""Human label review for mined cases. Labels are ESTIMATES; this records a person's check of them.
Usage:
  python review_labels.py --cases ../cases --list                 # show review status of every case
  python review_labels.py --cases ../cases --show case-1a2b3c4d   # show the evidence for one case
  python review_labels.py --cases ../cases --set case-1a2b3c4d=valid [--set case-...=invalid ...]
Verdicts: valid (label is right), invalid (label is wrong, e.g. the fix was unrelated), unclear.
For a positive: valid means the later fix really addresses a flaw the original change should have avoided.
For a negative: valid means the commit really looks sound. Review WITHOUT asking the AI being benchmarked.
score.py ignores invalid cases by default and scores only valid ones with --verified-only."""
import argparse, glob, json, os, subprocess

VERDICTS = ("valid", "invalid", "unclear")

def load(d):
    return {json.load(open(f, encoding="utf-8"))["id"]: f for f in glob.glob(os.path.join(d, "*.json"))}

def git(repo, *a):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", required=True)
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--show")
    ap.add_argument("--set", action="append", default=[], help="case-id=valid|invalid|unclear")
    a = ap.parse_args()
    files = load(a.cases)
    if not files: raise SystemExit("no cases in " + a.cases)
    for spec in a.set:
        cid, _, v = spec.partition("=")
        if cid not in files: raise SystemExit(f"unknown case {cid}")
        if v not in VERDICTS: raise SystemExit(f"verdict must be one of {VERDICTS}")
        c = json.load(open(files[cid], encoding="utf-8")); c["label_check"] = v
        json.dump(c, open(files[cid], "w", encoding="utf-8"), ensure_ascii=False, indent=1)
        print(f"{cid}: label_check={v}")
    if a.show:
        if a.show not in files: raise SystemExit(f"unknown case {a.show}")
        c = json.load(open(files[a.show], encoding="utf-8"))
        print(f"{c['id']}  label={c['label']} ({c['reason']})  date={c['date']}\n  subject: {c['subject']}\n  files: {', '.join(c['files'][:8])}")
        print("\n--- the change:\n" + git(c["repo"], "show", "--stat", "--no-color", "--pretty=format:%h %s", c["commit"]))
        if c.get("evidence_commit"):
            print("\n--- the later commit used as evidence:\n" + git(c["repo"], "show", "--no-color", "--pretty=format:%h %s%n%b", c["evidence_commit"])[:2500])
        else:
            print("\n--- no later fix or revert was found for this commit (control)")
    if a.list or not (a.set or a.show):
        counts = {}
        for cid in sorted(files):
            c = json.load(open(files[cid], encoding="utf-8")); v = c.get("label_check", "unreviewed")
            counts[v] = counts.get(v, 0) + 1
            print(f"{cid}  {c['label']:8} {v:10} {c['subject'][:60]}")
        print("summary:", counts)

if __name__ == "__main__":
    main()
