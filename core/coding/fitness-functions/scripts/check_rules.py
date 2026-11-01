#!/usr/bin/env python3
"""Run architectural fitness rules from a JSON file; exit 1 on any violation (CI-ready).

Usage: python scripts/check_rules.py <rules.json> [<repo_root>]
Rule types (every rule needs "id" and "why"; optional "allow": [file globs] = documented exceptions):
  forbid_import   {"type":"forbid_import","from":"<file glob>","to":"<regex on module name>"}
  max_file_lines  {"type":"max_file_lines","glob":"<file glob>","max":400}
  forbid_pattern  {"type":"forbid_pattern","glob":"<file glob>","regex":"<per-line regex>"}
Globs match the repo-relative path (fnmatch, "*" crosses "/"). Standard library only.
"""
import ast, fnmatch, json, os, re, sys

SKIP = {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "dist"}
PY_IMP = re.compile(r"^\s*(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.M)
JS_IMP = re.compile(r"""(?:from\s+|require\(\s*|import\(\s*|import\s+)['"]([^'"]+)['"]""")
TYPES = ("forbid_import", "max_file_lines", "forbid_pattern")


def match(rel, pat):
    return fnmatch.fnmatch(rel, pat) or fnmatch.fnmatch(os.path.basename(rel), pat)


def imports(path):
    txt = open(path, errors="ignore").read()
    if path.endswith(".py"):
        try:
            res = []
            for n in ast.walk(ast.parse(txt)):
                if isinstance(n, ast.Import):
                    res += [(a.name, n.lineno) for a in n.names]
                elif isinstance(n, ast.ImportFrom) and n.module and not n.level:
                    res.append((n.module, n.lineno))
            return res
        except SyntaxError:
            pass
    rx = PY_IMP if path.endswith(".py") else JS_IMP if path.endswith((".js", ".jsx", ".ts", ".tsx", ".mjs")) else None
    if not rx:
        return []
    return [(next(g for g in m.groups() if g), txt[:m.start()].count("\n") + 1) for m in rx.finditer(txt)]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    rules = json.load(open(sys.argv[1]))
    root = sys.argv[2] if len(sys.argv) > 2 else "."
    bad = [r.get("id", "?") for r in rules if not r.get("id") or not r.get("why") or r.get("type") not in TYPES]
    if bad:
        sys.exit(f"invalid rules (need id, why, known type): {bad}")
    files = []
    for r, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        files += [(os.path.join(r, f), os.path.relpath(os.path.join(r, f), root).replace("\\", "/")) for f in fs]
    viol = []
    for rule in rules:
        for path, rel in files:
            if any(match(rel, a) for a in rule.get("allow", [])):
                continue
            t = rule["type"]
            if t == "forbid_import" and match(rel, rule["from"]):
                viol += [(rule["id"], f"{rel}:{ln}", f"imports {mod}", rule["why"])
                         for mod, ln in imports(path) if re.search(rule["to"], mod)]
            elif t == "max_file_lines" and match(rel, rule["glob"]):
                n = sum(1 for _ in open(path, errors="ignore"))
                if n > rule["max"]:
                    viol.append((rule["id"], rel, f"{n} lines > {rule['max']}", rule["why"]))
            elif t == "forbid_pattern" and match(rel, rule["glob"]):
                viol += [(rule["id"], f"{rel}:{i}", l.strip()[:80], rule["why"])
                         for i, l in enumerate(open(path, errors="ignore"), 1) if re.search(rule["regex"], l)]
    for v in viol:
        print(f"VIOLATION {v[0]} {v[1]}: {v[2]}  [why: {v[3]}]")
    print(f"{len(rules)} rules, {len(viol)} violations")
    sys.exit(1 if viol else 0)


if __name__ == "__main__":
    main()
