#!/usr/bin/env python3
"""Find hidden coupling: which modules keep changing in the same commit.

Usage: python scripts/cochange.py <repo_dir> [--src SUBDIR] [--depth N] [--n 500] [--max-files 30] [--min 3]
Reads the last --n commits (git log), maps each changed file to a module (first N dirs under
--src, default repo root), ignores commits touching more than --max-files files (mass
renames/formatting are noise) and prints module pairs that changed together >= --min times.
strength = together / min(changes_of_A, changes_of_B); near 1.0 means one never changes alone.
Standard library + git. Evidence of coupling, not proof: ask WHY they co-change.
"""
import collections, itertools, subprocess, sys


def arg(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        sys.exit(__doc__)
    repo, src = sys.argv[1], arg("--src", "").strip("/")
    depth, n, max_files, min_t = int(arg("--depth", 1)), int(arg("--n", 500)), int(arg("--max-files", 30)), int(arg("--min", 3))
    out = subprocess.run(["git", "-C", repo, "log", "--name-only", "--pretty=format:@@@%H", "-n", str(n)],
                         capture_output=True, text=True)
    if out.returncode:
        sys.exit("git failed: " + out.stderr.strip())
    commits, cur = [], None
    for line in out.stdout.splitlines():
        if line.startswith("@@@"):
            cur = []; commits.append(cur)
        elif line.strip() and cur is not None:
            cur.append(line.strip())
    solo, pair, used, skipped = collections.Counter(), collections.Counter(), 0, 0
    for files in commits:
        if len(files) > max_files:
            skipped += 1; continue
        mods = set()
        for f in files:
            if src and not f.startswith(src + "/"):
                continue
            parts = (f[len(src) + 1:] if src else f).split("/")[:-1]
            mods.add("/".join(parts[:depth]) or "(root)")
        if not mods:
            continue
        used += 1
        solo.update(mods)
        pair.update(itertools.combinations(sorted(mods), 2))
    print(f"commits read: {len(commits)} | used: {used} | skipped as noise (> {max_files} files): {skipped}")
    rows = [(t / min(solo[a], solo[b]), t, a, b) for (a, b), t in pair.items() if t >= min_t]
    for strength, t, a, b in sorted(rows, reverse=True)[:25]:
        print(f"  strength={strength:.2f} together={t:<3} {a}  <->  {b}   (changes: {solo[a]}, {solo[b]})")
    if not rows:
        print("  no pair reached the threshold")


if __name__ == "__main__":
    main()
