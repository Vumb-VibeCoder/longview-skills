#!/usr/bin/env python3
"""Offline dependency scanner: finds pinning/lockfile/source risks measurable from files.

Usage: python scripts/dep_scan.py <project_dir> [--json]
Reads requirements*.txt, pyproject.toml ([project].dependencies), package.json and
detects lockfiles. Standard library only. It CANNOT see abandonment, deprecation or
CVEs: the skill procedure gathers those from upstream with cited evidence.
Statuses: PINNED, COMPATIBLE_RANGE (~=, ^, ~), RANGE (>=, <, ...), UNPINNED, SOURCE_URL.
"""
import json, os, re, sys

SKIP = {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "dist"}
LOCKS = {"package-lock.json", "yarn.lock", "pnpm-lock.yaml", "poetry.lock", "uv.lock", "Pipfile.lock"}
URL = re.compile(r"^(git\+|git:|https?://|file:|\.{0,2}/)")


def classify_py(spec):
    s = spec.strip()
    if not s:
        return "UNPINNED"
    if "==" in s and "*" not in s:
        return "PINNED"
    if "~=" in s:
        return "COMPATIBLE_RANGE"
    return "RANGE"


def classify_js(ver):
    v = ver.strip()
    if re.match(r"^(git|github:|https?:|file:|link:)", v) or re.match(r"^[\w.-]+/[\w.-]+(#.*)?$", v):
        return "SOURCE_URL"
    if v in ("", "*", "latest") or v.startswith((">", "<")) or re.search(r"(^|\.)[xX*]($|\.)", v):
        return "UNPINNED" if v in ("", "*", "latest") or "x" in v.lower() else "RANGE"
    if v[0] in "^~":
        return "COMPATIBLE_RANGE"
    return "PINNED" if re.match(r"^\d+\.\d+\.\d+", v) else "RANGE"


def parse_requirement(t):
    t = t.strip()
    if t.startswith("-e "):
        t = t[3:].strip()
    if URL.match(t) or " @ " in t:
        return t, "SOURCE_URL"
    m = re.match(r"^([A-Za-z0-9_.\-]+)(\[[^\]]*\])?\s*(.*)$", t)
    if not m:
        return t, "UNPINNED"
    return m.group(1), classify_py(m.group(3).split(";")[0])


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = sys.argv[1]
    manifests, deps, lock_dirs = [], [], set()
    for r, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        rel_dir = os.path.relpath(r, root)
        for f in files:
            p = os.path.join(r, f)
            rel = os.path.normpath(os.path.join(rel_dir, f))
            if f in LOCKS:
                lock_dirs.add(rel_dir)
            elif re.match(r"requirements.*\.txt$", f):
                manifests.append(rel)
                for i, line in enumerate(open(p, errors="ignore", encoding="utf-8"), 1):
                    t = line.split(" #")[0].strip()
                    if not t or t.startswith("#") or t.startswith(("-r", "-c", "--")):
                        continue
                    name, st = parse_requirement(t)
                    deps.append({"file": rel, "line": i, "name": name, "spec": t, "status": st})
            elif f == "pyproject.toml":
                manifests.append(rel)
                m = re.search(r"^dependencies\s*=\s*\[(.*?)\]", open(p, errors="ignore", encoding="utf-8").read(), re.S | re.M)
                for item in re.findall(r"[\"']([^\"']+)[\"']", m.group(1)) if m else []:
                    name, st = parse_requirement(item)
                    deps.append({"file": rel, "line": 0, "name": name, "spec": item, "status": st})
            elif f == "package.json":
                manifests.append(rel)
                try:
                    data = json.load(open(p, encoding="utf-8"))
                except Exception:
                    continue
                for sect in ("dependencies", "devDependencies", "peerDependencies"):
                    for k, v in (data.get(sect) or {}).items():
                        deps.append({"file": rel, "line": 0, "name": k, "spec": f"{k}@{v}", "section": sect, "status": classify_js(str(v))})
    counts = {}
    for d in deps:
        counts[d["status"]] = counts.get(d["status"], 0) + 1
    risky = [d for d in deps if d["status"] in ("UNPINNED", "SOURCE_URL", "RANGE")]
    no_lock = sorted({os.path.dirname(m) or "." for m in manifests} - lock_dirs)
    out = {"manifests": manifests, "direct_dependencies": len(deps), "status_counts": counts,
           "risky": risky, "manifest_dirs_without_lockfile": no_lock}
    if "--json" in sys.argv:
        print(json.dumps(out, indent=2))
        return
    print(f"manifests: {len(manifests)} | direct deps: {len(deps)} | {counts}")
    for d in risky:
        print(f"  {d['status']:<12} {d['file']}:{d['line']}  {d['spec']}")
    for d in no_lock:
        print(f"  NO_LOCKFILE  {d}")
    if not manifests:
        print("no manifests found: ask where dependencies are declared")


if __name__ == "__main__":
    main()
