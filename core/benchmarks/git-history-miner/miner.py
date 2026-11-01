#!/usr/bin/env python3
"""Mine git history into short-sightedness benchmark cases with REAL ANSWERS.

Positive: a commit that was later
  - reverted (a "Revert ..." commit points at it), or
  - patched: at least one "fix" commit touches the same file within --window days afterwards.
Negative (control): a commit that was not reverted or patched within --clean-days days
  and is old enough to have been observed for that long. Used to measure false alarms.

Usage:
  python miner.py <git_repo> --out ../cases [--window 14] [--clean-days 60] [--max 40]
Uses only git and the standard library.
"""
import argparse, json, os, re, subprocess, sys, datetime, random

FIX_RE = re.compile(r"\b(fix|bug|hotfix|patch|oops|revert|regress)", re.I)
# Label-noise filters (found by running on a real repo: dependency bumps were labelled "patched" because an
# unrelated fix touched go.mod/go.sum, and "Fix lint" / "Fix typo" were counted as evidence of short-sightedness).
BOT_RE = re.compile(r"^(build|chore|ci)\(deps[^)]*\)|^bump\b|^update dependency|^\[?dependabot|^renovate", re.I)
NOISE_FIX_RE = re.compile(r"\b(lint|typo|format|formatting|style|whitespace|spelling|comment|readme|docs?|changelog|ci)\b", re.I)
IGNORED_FILE_RE = re.compile(r"(^|/)(go\.sum|go\.mod|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|Gemfile\.lock|composer\.lock)$|^\.github/|\.md$|^docs?/|(^|/)LICENSE", re.I)
SEP = "\x1e"
FIELD = "\x1f"


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def changed_files(repo, sha):
    out = git(repo, "show", "--no-merges", "--name-only", "--pretty=format:", sha)
    return [l for l in out.splitlines() if l.strip()]


def code_files(c):
    """Files that carry real decisions: lockfiles, CI config and docs are ignored."""
    return {f for f in c["files"] if not IGNORED_FILE_RE.search(f)}


def is_candidate(c):
    return bool(c["parent"]) and not FIX_RE.search(c["subject"]) and not BOT_RE.search(c["subject"]) and bool(code_files(c))


def is_real_fix(c):
    return bool(FIX_RE.search(c["subject"])) and not NOISE_FIX_RE.search(c["subject"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo")
    ap.add_argument("--out", default="../cases")
    ap.add_argument("--window", type=int, default=14)
    ap.add_argument("--clean-days", type=int, default=60)
    ap.add_argument("--max", type=int, default=40)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    random.seed(a.seed)
    os.makedirs(a.out, exist_ok=True)

    shas = git(a.repo, "log", "--no-merges", "--pretty=format:%H").split()
    meta = {}
    for sha in shas:
        o = git(a.repo, "show", "-s", f"--pretty=format:%P{FIELD}%at{FIELD}%s{FIELD}%b", sha)
        p = o.split(FIELD)
        meta[sha] = dict(sha=sha, parent=(p[0].split() or [None])[0], ts=int(p[1]), subject=p[2], body=FIELD.join(p[3:]))
        meta[sha]["files"] = changed_files(a.repo, sha)
    ordered = sorted(meta.values(), key=lambda c: c["ts"])
    if not ordered:
        print("The repo has no commits.")
        return 1
    newest = ordered[-1]["ts"]

    positives = {}
    # 1) revert
    for c in ordered:
        m = re.search(r"This reverts commit ([0-9a-f]{7,40})", c["body"])
        if m:
            target = next((s for s in meta if s.startswith(m.group(1))), None)
            if target and target not in positives and meta[target]["parent"]:
                positives[target] = dict(reason="revert", evidence=c["sha"], evidence_subject=c["subject"])
    # 2) patched: a fix touching the same file inside the window
    for i, c in enumerate(ordered):
        if c["sha"] in positives or not is_candidate(c):
            continue
        for later in ordered[i + 1:]:
            if later["ts"] - c["ts"] > a.window * 86400:
                break
            if is_real_fix(later) and code_files(later) & code_files(c):
                positives[c["sha"]] = dict(reason="patched-soon", evidence=later["sha"], evidence_subject=later["subject"])
                break

    # negatives: not patched or reverted, and old enough to observe
    negatives = []
    for i, c in enumerate(ordered):
        if c["sha"] in positives or not is_candidate(c):
            continue
        if newest - c["ts"] < a.clean_days * 86400 or not c["files"]:
            continue
        window_end = c["ts"] + a.clean_days * 86400
        bad = any(l["ts"] <= window_end and l["ts"] > c["ts"] and is_real_fix(l) and code_files(l) & code_files(c) for l in ordered[i + 1:])
        if not bad:
            negatives.append(c["sha"])

    pos_ids = list(positives)
    random.shuffle(pos_ids)
    random.shuffle(negatives)
    pos_ids = pos_ids[: a.max // 2 or 1]
    negatives = negatives[: len(pos_ids)]

    n = 0
    for label, ids in (("positive", pos_ids), ("negative", negatives)):
        for sha in ids:
            c = meta[sha]
            case = dict(
                id=f"case-{sha[:8]}", label=label, commit=sha, parent=c["parent"],
                subject=c["subject"], files=c["files"][:30],
                reason=positives.get(sha, {}).get("reason", "clean"),
                evidence_commit=positives.get(sha, {}).get("evidence"),
                evidence_subject=positives.get(sha, {}).get("evidence_subject"),
                repo=os.path.abspath(a.repo),
                date=datetime.datetime.fromtimestamp(c["ts"]).strftime("%Y-%m-%d"),
            )
            json.dump(case, open(os.path.join(a.out, case["id"] + ".json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
            n += 1
    print(f"Found {len(positives)} positives and {len(negatives)} usable controls; wrote {n} cases to {a.out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print("git error:", e)
        sys.exit(2)
