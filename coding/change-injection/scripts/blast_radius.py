#!/usr/bin/env python3
"""Measure the blast radius of an injected change from git.

Usage: python scripts/blast_radius.py <repo> [--base REF] [--head REF] [--src DIR] [--depth N]
Default: compare the WORKING TREE (including untracked new files) with --base (default HEAD).
With --head: compare two refs/commits instead (e.g. --base main --head experiment-branch).
Counted toward the radius: EXISTING non-test files that were modified or deleted, mapped to modules
(first --depth directories under --src, default repo root; files directly in --src = "(root)").
NEW files, test files and noise (lockfiles, snapshots, minified/generated, dist/build) are listed
separately and never inflate the radius. Radius = number of distinct modules edited.
Suggested score for verdict-format "Change tolerance" for ONE scenario: 1 module -> 3,
2 -> 2, 3-4 -> 1, 5+ -> 0 (use the median across scenarios and report the worst case).
Standard library + git.
"""
import fnmatch, subprocess, sys

NOISE = ["*.lock", "package-lock.json", "yarn.lock", "pnpm-lock.yaml", "*.min.js", "*.min.css", "*.snap", "*/__snapshots__/*",
         "dist/*", "build/*", "*/dist/*", "*/build/*", "*.pyc", "*.map"]


def arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


def git(repo, *a):
    r = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    if r.returncode:
        sys.exit("git error: " + r.stderr.strip())
    return r.stdout


def is_test(p):
    parts = p.split("/")
    return any(x in ("tests", "test", "__tests__", "spec") for x in parts[:-1]) or parts[-1].startswith("test_") or ".test." in parts[-1] or parts[-1].endswith(("_test.py", "_spec.rb"))


def main():
    if len(sys.argv) < 2 or sys.argv[1].startswith("--"):
        sys.exit(__doc__)
    repo, base, head = sys.argv[1], arg("--base", "HEAD"), arg("--head")
    src, depth = (arg("--src", "") or "").strip("/"), int(arg("--depth", 1))
    rng = [base, head] if head else [base]
    status = git(repo, "diff", "--name-status", "-M", *rng).splitlines()
    nums = {}
    for line in git(repo, "diff", "--numstat", "-M", *rng).splitlines():
        a, d, f = line.split("\t", 2)
        nums[f.split(" => ")[-1].strip("{} ")] = (0 if a == "-" else int(a), 0 if d == "-" else int(d))
    entries = []
    for line in status:
        parts = line.split("\t")
        code, path = parts[0][0], parts[-1]
        entries.append((code, path))
    if not head:
        for p in git(repo, "ls-files", "--others", "--exclude-standard").splitlines():
            entries.append(("A", p))
            try:
                n = sum(1 for _ in open(f"{repo}/{p}", errors="ignore")); nums[p] = (n, 0)
            except OSError:
                pass
    mods, edited, added, tests, noise = {}, [], [], [], []
    for code, p in entries:
        if any(fnmatch.fnmatch(p, g) for g in NOISE):
            noise.append(p); continue
        if is_test(p):
            tests.append((code, p)); continue
        if src and not p.startswith(src + "/"):
            continue
        if code == "A":
            added.append(p); continue
        edited.append(p)
        rel = p[len(src) + 1:] if src else p
        d = rel.split("/")[:-1]
        mods.setdefault("/".join(d[:depth]) or "(root)", []).append(p)
    counted = edited + added
    add = sum(nums.get(p, (0, 0))[0] for p in counted); rem = sum(nums.get(p, (0, 0))[1] for p in counted)
    print(f"compared: {' .. '.join(rng) if head else base + ' .. WORKING TREE (+ untracked)'}")
    print(f"RADIUS (modules edited): {len(mods)} | existing files edited: {len(edited)} | source lines +{add} -{rem} (excl. tests/noise)")
    for m, fs in sorted(mods.items()):
        print(f"  module {m}: {len(fs)} file(s): {', '.join(sorted(fs))[:140]}")
    print(f"new files (not in radius): {len(added)} {added[:8]}")
    print(f"test files touched: {len(tests)} {[p for _, p in tests][:8]}")
    print(f"ignored as noise: {len(noise)}")
    r = len(mods)
    print("suggested single-scenario score:", 3 if r <= 1 else 2 if r == 2 else 1 if r <= 4 else 0, "(see docstring)")


if __name__ == "__main__":
    main()
