#!/usr/bin/env python3
"""Rank hotspots: files that change often AND are big AND keep needing fixes.

Usage: python scripts/hotspots.py <repo> [--since "12 months ago"] [--src DIR] [--top 10] [--max-files 30]
churn      = commits touching the file in the window (commits touching more than --max-files files are
             ignored as bulk noise: renames, formatting)
lines      = current line count (files that no longer exist are skipped)
fix_commits= commits whose subject matches fix|bug|hotfix|revert|workaround|patch (case-insensitive)
score      = percentile(churn) x percentile(lines), both within the analysed files (0..1).
A high score means "expensive and changing": the best place to spend review effort first. It
does not prove the code is bad. Standard library + git.
"""
import collections, os, re, subprocess, sys

CODE = (".py", ".js", ".jsx", ".ts", ".tsx", ".java", ".go", ".rb", ".rs", ".cs", ".php", ".kt", ".swift", ".c", ".cc", ".cpp", ".h", ".sql")
FIX = re.compile(r"\b(fix|fixes|fixed|bug|hotfix|revert|workaround|patch)\b", re.I)


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def pct(values):
    order = sorted(values)
    return {v: (order.index(v) + order.count(v) / 2) / len(order) for v in set(values)}


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        sys.exit(__doc__)
    repo, since = sys.argv[1], arg("--since", "12 months ago")
    src, top, maxf = arg("--src", "").strip("/"), int(arg("--top", 10)), int(arg("--max-files", 30))
    r = subprocess.run(["git", "-C", repo, "log", f"--since={since}", "--name-only", "--pretty=format:@@@%s"], capture_output=True, text=True)
    if r.returncode:
        sys.exit("git failed: " + r.stderr.strip())
    commits, cur = [], None
    for line in r.stdout.splitlines():
        if line.startswith("@@@"):
            cur = [line[3:], []]; commits.append(cur)
        elif line.strip() and cur is not None:
            cur[1].append(line.strip())
    churn, fixes, skipped = collections.Counter(), collections.Counter(), 0
    for subj, files in commits:
        if len(files) > maxf:
            skipped += 1; continue
        for f in files:
            if f.endswith(CODE) and (not src or f.startswith(src + "/")):
                churn[f] += 1
                if FIX.search(subj):
                    fixes[f] += 1
    size = {}
    for f in churn:
        p = os.path.join(repo, f)
        if os.path.isfile(p):
            size[f] = sum(1 for _ in open(p, errors="ignore", encoding="utf-8"))
    files = [f for f in churn if f in size]
    if not files:
        print(f"no changed code files in the window ({len(commits)} commits, {skipped} skipped as bulk)"); return
    pc, ps = pct([churn[f] for f in files]), pct([size[f] for f in files])
    rows = sorted(((pc[churn[f]] * ps[size[f]], f) for f in files), reverse=True)[:top]
    print(f"window: since {since} | commits: {len(commits)} | bulk commits skipped: {skipped} | files analysed: {len(files)}")
    print(f"{'score':>6} {'churn':>6} {'lines':>6} {'fix':>4}  file")
    for s, f in rows:
        print(f"{s:>6.2f} {churn[f]:>6} {size[f]:>6} {fixes[f]:>4}  {f}")
    if len(files) < 10:
        print("NOTE: fewer than 10 files analysed; percentiles are coarse.")


if __name__ == "__main__":
    main()
