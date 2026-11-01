#!/usr/bin/env python3
"""Mine git history into short-sightedness benchmark cases with REAL ANSWERS.

Positive: a commit that was later
  - reverted (a "Revert ..." commit points at it), or
  - patched: a "fix" commit within --window days REMOVES OR REWRITES lines that this commit introduced
    (found with git blame on the fix's parent, so an unrelated fix in the same file no longer counts).
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
NOISE_FIX_RE = re.compile(r"\b(lint|typo|format|formatting|style|whitespace|spelling|comment|readme|docs?|changelog|ci|pydocstyle|flake8|pylint|rst|docstrings?|examples?|xfail|ensure the test)\b", re.I)
IGNORED_FILE_RE = re.compile(r"(^|/)(go\.sum|go\.mod|package-lock\.json|yarn\.lock|pnpm-lock\.yaml|poetry\.lock|Cargo\.lock|Gemfile\.lock|composer\.lock)$|^\.github/|\.md$|^docs?/|(^|/)LICENSE", re.I)
# v2: release/version-bump/housekeeping commits carry no design decision, whatever happens to them later.
NOISE_SUBJECT_RE = re.compile(r"^(start version|documentation|apply format|this is\b|ready for\b|release\b|update dev|version\b|prepare\b|merge\b|update (pre-commit|requirements|dependencies|changelog|version)|pre-commit|typo\b|bump\b|v?\d+\.\d+)|\b(version bump|dev version|release notes|pre-commit|autopep8|whitespace|cleanup|xfails?|reexports?)\b", re.I)
CODE_EXT_RE = re.compile(r"\.(py|js|jsx|ts|tsx|go|rs|java|kt|c|h|cc|cpp|hpp|cs|rb|php|swift|scala|sh)$", re.I)
MAX_ADDED = 400  # larger commits do not fit a review prompt and mix many decisions
MIN_ADDED = 3  # a commit that adds fewer lines than this is too small to judge
SEP = "\x1e"
FIELD = "\x1f"


def git(repo, *args):
    r = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0:
        raise RuntimeError(r.stderr.strip())
    return r.stdout


def changed_files(repo, sha):
    """Return (files, added_lines) using --numstat in one call."""
    out = git(repo, "show", "--no-merges", "--numstat", "--pretty=format:", sha)
    files, added = [], 0
    for l in out.splitlines():
        p = l.split("\t")
        if len(p) == 3:
            files.append(p[2])
            if p[0].isdigit():
                added += int(p[0])
    return files, added


def removed_ranges(repo, sha):
    """{file: [(start, count)]} of OLD-side line ranges the commit removed or rewrote (pure additions are skipped)."""
    out = git(repo, "show", "--no-merges", "-U0", "--pretty=format:", sha)
    res, cur = {}, None
    for l in out.splitlines():
        if l.startswith("--- "):
            cur = None if l.startswith("--- /dev/null") else l[6:] if l.startswith("--- a/") else None
        elif l.startswith("@@") and cur:
            m = re.match(r"@@ -(\d+)(?:,(\d+))? ", l)
            if m:
                start, cnt = int(m.group(1)), int(m.group(2) if m.group(2) is not None else 1)
                if cnt > 0:
                    res.setdefault(cur, []).append((start, cnt))
    return res


def blamed_origins(repo, fix_sha, ranges):
    """Set of commits that introduced the lines the fix removed (git blame on the fix's parent)."""
    origins = set()
    for f, rs in ranges.items():
        if not CODE_EXT_RE.search(f):
            continue
        args = ["blame", "--porcelain"]
        for st, cnt in rs[:20]:
            args += ["-L", f"{st},{st + cnt - 1}"]
        try:
            out = git(repo, *args, fix_sha + "^", "--", f)
        except RuntimeError:
            continue  # renamed or too-short file: cannot attribute, skip rather than guess
        for l in out.splitlines():
            m = re.match(r"^([0-9a-f]{40}) \d+ \d+", l)
            if m:
                origins.add(m.group(1))
    return origins


def code_files(c):
    """Files that carry real decisions: lockfiles, CI config, docs and non-code files are ignored."""
    return {f for f in c["files"] if not IGNORED_FILE_RE.search(f) and CODE_EXT_RE.search(f)}


def is_candidate(c):
    return (bool(c["parent"]) and not FIX_RE.search(c["subject"]) and not BOT_RE.search(c["subject"])
            and not NOISE_SUBJECT_RE.search(c["subject"]) and bool(code_files(c)) and MIN_ADDED <= c.get("added", 0) <= MAX_ADDED)


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
        meta[sha]["files"], meta[sha]["added"] = changed_files(a.repo, sha)
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
    # 2) patched: a real fix whose REMOVED lines were introduced by an earlier candidate (git blame), inside the window.
    #    hit[sha] = smallest delay in days between the candidate and a fix that rewrote its lines.
    hit = {}
    for c in ordered:
        if not is_real_fix(c) or not c["parent"] or not code_files(c):
            continue
        for origin in blamed_origins(a.repo, c["sha"], removed_ranges(a.repo, c["sha"])):
            o = meta.get(origin)
            if not o or origin == c["sha"] or not is_candidate(o):
                continue
            days = (c["ts"] - o["ts"]) / 86400
            if 0 < days and (origin not in hit or days < hit[origin][0]):
                hit[origin] = (days, c["sha"], c["subject"])
    for origin, (days, fsha, fsub) in hit.items():
        if origin not in positives and days <= a.window:
            positives[origin] = dict(reason="patched-soon", evidence=fsha, evidence_subject=fsub)

    # negatives: nobody rewrote their lines within --clean-days, and they are old enough to observe
    negatives = []
    for c in ordered:
        if c["sha"] in positives or not is_candidate(c):
            continue
        if newest - c["ts"] < a.clean_days * 86400:
            continue
        if c["sha"] in hit and hit[c["sha"]][0] <= a.clean_days:
            continue
        negatives.append(c["sha"])

    n_pos_total, n_neg_total = len(positives), len(negatives)
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
    print(f"Found {n_pos_total} positives and {n_neg_total} usable controls in the repo; wrote {n} cases to {a.out}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print("git error:", e)
        sys.exit(2)
