#!/usr/bin/env python3
"""Measure a unified diff (a pull request or commit range) and flag review risks. Standard library only.

Usage:
  python scripts/diff_stats.py [FILE | -]  [--json] [--max-lines N] [--max-files N]
  python scripts/diff_stats.py --git <range> [--json]      (runs: git diff --no-color <range>)
FILE or stdin must hold a unified diff (`git diff`, `git show`, a .diff/.patch file).
Exit codes: 0 no flags, 1 flags raised, 2 bad input.
Flags are CANDIDATES for a reviewer to confirm; secret values are masked in the output.

Flags:
  D01  source changed, no test file changed
  D02  diff too large to review as one change (default: over 400 changed lines or 15 files)
  D03  change spreads across 4 or more top-level directories
  D04  dependency manifest changed (lists added dependency lines) or manifest and lockfile out of step
  D05  migration, schema or SQL file touched (needs a way back)
  D06  tests weakened: test file deleted, assertions removed, skip/xfail added
  D07  risky lines added: bare except, swallowed error, TODO/FIXME, debug leftovers, hard-coded secret, TLS off, eval/exec
  D08  generated, build or minified files changed
"""
import collections, json, os, re, subprocess, sys

MAX_LINES, MAX_FILES = 400, 15

LOCKS = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "pipfile.lock", "go.sum", "cargo.lock", "gemfile.lock", "composer.lock", "uv.lock"}
MANIFESTS = {"package.json", "pyproject.toml", "go.mod", "cargo.toml", "gemfile", "pom.xml", "composer.json", "pipfile", "setup.py", "setup.cfg", "build.gradle"}
DEP_ADD = re.compile(r"^\s*[\"']?[A-Za-z0-9@][\w./@-]*[\"']?\s*(?:[=<>~!^]=?|:|\s)\s*[\"']?[\w.^~<>=*-]+")
SECRET = re.compile(r"(?i)[\w-]*(?:api[_-]?key|secret|token|passwd|password|private[_-]?key)[\w-]*[\"']?\s*[:=]\s*[\"'](?!https?://)([^\"'\s]{8,})[\"']")
RISKY = [
    ("bare or swallowed except", re.compile(r"^\s*except\s*:|except\s+(?:Exception|BaseException)\b.*:\s*pass|catch\s*\([^)]*\)\s*\{\s*\}")),
    ("TODO/FIXME/HACK added", re.compile(r"\b(?:TODO|FIXME|HACK|XXX)\b")),
    ("debug leftover", re.compile(r"\bbreakpoint\(\)|\bpdb\.set_trace\(|\bconsole\.log\(|^\s*debugger\s*;?\s*$|^\s*print\(")),
    ("TLS check off", re.compile(r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false|InsecureSkipVerify\s*:\s*true")),
    ("eval/exec on a value", re.compile(r"(?<![\w.])(?:eval|exec)\(")),
]
SKIP_ADDED = re.compile(r"pytest\.mark\.(?:skip|xfail)|unittest\.skip|\bxit\(|\bxdescribe\(|\bit\.skip\(|\btest\.skip\(|@Ignore\b|\.only\(")
ASSERT = re.compile(r"\bassert\w*\b|\bexpect\(|\bshould\b|\.toBe|\.toEqual|\bpytest\.raises")


def categorize(path):
    p = path.replace("\\", "/")
    low, base = p.lower(), os.path.basename(p).lower()
    parts = low.split("/")
    if base in LOCKS:
        return "lock"
    if base in MANIFESTS or re.match(r"requirements[\w.-]*\.txt$", base):
        return "manifest"
    if any(x in parts for x in ("dist", "build", "node_modules", "__generated__", "generated")) or base.endswith((".min.js", ".min.css", ".pb.go", ".map")):
        return "generated"
    if any(x in parts for x in ("migrations", "migrate", "alembic")) or base.endswith(".sql") or base.startswith("schema."):
        return "migration"
    if any(x in parts for x in ("tests", "test", "__tests__", "spec")) or re.search(r"(^test_|_test\.|\.test\.|\.spec\.)", base):
        return "test"
    if base.endswith((".md", ".rst", ".txt", ".adoc")) or "docs" in parts:
        return "docs"
    if ".github" in parts or base in ("dockerfile", "makefile", ".gitignore", ".editorconfig") or base.endswith((".yml", ".yaml", ".toml", ".ini", ".cfg", ".json", ".env")):
        return "config"
    return "source"


def parse_diff(text):
    files, cur, new_line = [], None, 0
    for raw in text.splitlines():
        if raw.startswith("diff --git "):
            m = re.match(r"diff --git a/(.+?) b/(.+)$", raw)
            path = m.group(2) if m else raw.split()[-1]
            cur = {"path": path, "added": 0, "removed": 0, "new": False, "deleted": False, "add_lines": [], "rem_lines": [], "binary": False}
            files.append(cur)
        elif cur is None:
            continue
        elif raw.startswith("new file mode"):
            cur["new"] = True
        elif raw.startswith("deleted file mode"):
            cur["deleted"] = True
        elif raw.startswith("Binary files") or raw.startswith("GIT binary patch"):
            cur["binary"] = True
        elif raw.startswith("+++ "):
            tgt = raw[4:].strip()
            if tgt != "/dev/null" and tgt.startswith("b/"):
                cur["path"] = tgt[2:]
        elif raw.startswith("@@"):
            m = re.match(r"@@ -\d+(?:,\d+)? \+(\d+)", raw)
            new_line = int(m.group(1)) if m else 0
        elif raw.startswith("+") and not raw.startswith("+++"):
            cur["added"] += 1
            cur["add_lines"].append((new_line, raw[1:]))
            new_line += 1
        elif raw.startswith("-") and not raw.startswith("---"):
            cur["removed"] += 1
            cur["rem_lines"].append(raw[1:])
        elif raw.startswith(" "):
            new_line += 1
    for f in files:
        f["category"] = categorize(f["path"])
    return files


def mask(s):
    return SECRET.sub(lambda m: m.group(0).replace(m.group(1), m.group(1)[:2] + "***"), s)


def analyse(files, max_lines, max_files):
    flags = []
    by_cat = collections.defaultdict(lambda: [0, 0, 0])  # files, added, removed
    for f in files:
        c = by_cat[f["category"]]
        c[0] += 1; c[1] += f["added"]; c[2] += f["removed"]
    total = sum(f["added"] + f["removed"] for f in files)
    src = [f for f in files if f["category"] == "source" and not f["deleted"]]
    tests = [f for f in files if f["category"] == "test"]
    if src and not tests and sum(f["added"] + f["removed"] for f in src) >= 5:
        flags.append(("D01", "-", f"{len(src)} source file(s) changed ({sum(f['added'] + f['removed'] for f in src)} lines), no test file changed: behaviour change without a test, or an untested refactor"))
    if total > max_lines or len(files) > max_files:
        flags.append(("D02", "-", f"{total} changed lines in {len(files)} files: too big to review as one change; ask for a split by concern"))
    tops = {f["path"].split("/")[0] if "/" in f["path"] else "." for f in files if f["category"] in ("source", "test", "config", "migration")}
    if len(tops) >= 4:
        flags.append(("D03", "-", f"change touches {len(tops)} top-level areas ({', '.join(sorted(tops)[:6])}): several concerns in one diff"))
    manifests = [f for f in files if f["category"] == "manifest"]
    locks = [f for f in files if f["category"] == "lock"]
    for f in manifests:
        adds = [(n, l.strip()) for n, l in f["add_lines"] if l.strip() and not l.strip().startswith(("#", "//", "{", "}", "[", "]")) and DEP_ADD.match(l)]
        flags.append(("D04", f["path"], f"dependency manifest changed (+{f['added']} -{f['removed']}); added entries: " + ("; ".join(a[1][:50] for a in adds[:5]) or "none that look like dependencies")))
    if manifests and not locks and any(os.path.basename(f["path"]).lower() in ("package.json", "pyproject.toml", "cargo.toml", "gemfile") for f in manifests):
        flags.append(("D04", "-", "manifest changed but no lockfile changed: installs may differ between machines"))
    if locks and not manifests:
        flags.append(("D04", locks[0]["path"], "lockfile changed with no manifest change: versions moved without a stated reason"))
    for f in files:
        if f["category"] == "migration":
            flags.append(("D05", f["path"], "migration or schema file changed: check the way back (expand-then-contract, backup, trigger)"))
        if f["category"] == "generated":
            flags.append(("D08", f["path"], "generated or build output in the diff: review the source instead, and keep it out of the change if possible"))
    for f in tests:
        if f["deleted"]:
            flags.append(("D06", f["path"], "test file deleted"))
            continue
        rem = sum(1 for l in f["rem_lines"] if ASSERT.search(l))
        add = sum(1 for _, l in f["add_lines"] if ASSERT.search(l))
        if rem > add:
            flags.append(("D06", f["path"], f"assertions removed ({rem}) exceed assertions added ({add}): tests may have been weakened to pass"))
        for n, l in f["add_lines"]:
            if SKIP_ADDED.search(l):
                flags.append(("D06", f"{f['path']}:{n}", "skip, xfail or .only added to a test: " + l.strip()[:60]))
    for f in files:
        if f["category"] in ("source", "config") and not f["deleted"]:
            for n, l in f["add_lines"]:
                for label, rx in RISKY:
                    if f["category"] == "config" and label != "TODO/FIXME/HACK added":
                        continue
                    if rx.search(l):
                        flags.append(("D07", f"{f['path']}:{n}", f"{label}: " + mask(l.strip())[:70]))
                if SECRET.search(l):
                    flags.append(("D07", f"{f['path']}:{n}", "possible hard-coded secret: " + mask(l.strip())[:70]))
    return by_cat, total, flags


def read_input(args):
    if "--git" in sys.argv:
        i = sys.argv.index("--git")
        if i + 1 >= len(sys.argv):
            raise SystemExit("error: --git needs a range, for example HEAD~1 or main...feature")
        r = subprocess.run(["git", "diff", "--no-color", sys.argv[i + 1]], capture_output=True, text=True)
        if r.returncode != 0:
            raise SystemExit("error: git diff failed: " + r.stderr.strip()[:200])
        return r.stdout
    if not args or args[0] == "-":
        return sys.stdin.read()
    try:
        return open(args[0], encoding="utf-8", errors="replace").read()
    except OSError as e:
        raise SystemExit(f"error: cannot read {args[0]}: {e.strerror}")


def intopt(name, default):
    if name in sys.argv:
        i = sys.argv.index(name)
        try:
            return int(sys.argv[i + 1])
        except (IndexError, ValueError):
            raise SystemExit(f"error: {name} needs a whole number")
    return default


def main():
    skip = set()
    for opt in ("--max-lines", "--max-files", "--git"):
        if opt in sys.argv:
            skip.add(sys.argv.index(opt) + 1)
    args = [a for i, a in enumerate(sys.argv[1:], 1) if i not in skip and (not a.startswith("--"))]
    try:
        max_lines, max_files = intopt("--max-lines", MAX_LINES), intopt("--max-files", MAX_FILES)
        text = read_input(args)
    except SystemExit as e:
        print(e, file=sys.stderr)
        return 2
    files = parse_diff(text)
    if not files:
        print("error: no files found: input is not a unified diff", file=sys.stderr)
        return 2
    by_cat, total, flags = analyse(files, max_lines, max_files)
    if "--json" in sys.argv:
        print(json.dumps({"files": [{k: f[k] for k in ("path", "category", "added", "removed", "new", "deleted")} for f in files],
                          "total_changed_lines": total, "flags": [dict(id=i, where=w, note=n) for i, w, n in flags]}, indent=1))
    else:
        print(f"{len(files)} files, {total} changed lines")
        for cat, (n, a, r) in sorted(by_cat.items()):
            print(f"  {cat:<10} {n:>3} files  +{a} -{r}")
        print()
        for f in files:
            tag = "new" if f["new"] else "deleted" if f["deleted"] else "binary" if f["binary"] else ""
            print(f"  {f['category']:<10} +{f['added']:<4} -{f['removed']:<4} {f['path']} {tag}".rstrip())
        print()
        for i, w, n in flags:
            print(f"[{i}] {w}  {n}")
        print(f"\n{len(flags)} flag(s):", dict(collections.Counter(i for i, _, _ in flags)))
    return 1 if flags else 0


if __name__ == "__main__":
    sys.exit(main())
