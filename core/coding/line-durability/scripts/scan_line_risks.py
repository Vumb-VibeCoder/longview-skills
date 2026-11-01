#!/usr/bin/env python3
"""Scan Python code for measurable short-sightedness candidates (maps to myopia-patterns M-IDs).

Usage: python scripts/scan_line_risks.py <file_or_dir> [--json]
Python only; standard library only. Output lines are CANDIDATES: each must be confirmed by reading
the code (see "Do NOT flag when" in myopia-patterns). Logic errors and business assumptions need
a human or a reasoning pass.

Detects:
  M01  hard-coded number / URL / absolute path (named UPPER_CASE constants, docstrings and test files are ignored)
  M03  bare except, except-BaseException, handler whose body is only pass / ...
  M04  duplicated block of >= 6 non-trivial lines across or within files (one report per duplicated region)
  M05  loops nested 3+ deep in one function; whole-input reads (.read(), .readlines())
  M06  `global` statement (hidden shared state / order dependence)
  M08  function longer than 60 lines, more than 6 parameters (self/cls excluded), 3+ boolean-default flags
  NOTE TODO/FIXME/HACK comments (unrecorded debt; not a myopia pattern by itself)
"""
import ast, collections, hashlib, json, os, sys

ALLOWED_NUMBERS = {0, 1, -1, 2, 100}
LONG_FUNC, MANY_ARGS, DUP_MIN_LINES, NEST_LIMIT = 60, 6, 6, 3
SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "dist"}


def iter_py(path):
    if os.path.isfile(path):
        yield path
        return
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in sorted(files):
            if f.endswith(".py"):
                yield os.path.join(root, f)


def is_test_path(p):
    parts = p.replace("\\", "/").split("/")
    return any(x in ("tests", "test") for x in parts[:-1]) or parts[-1].startswith(("test_", "conftest")) or parts[-1].endswith("_test.py")


def loop_depth_report(fn):
    best = (0, None)

    def walk(node, depth, outer):
        nonlocal best
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda, ast.ClassDef)):
                continue
            if isinstance(child, (ast.For, ast.AsyncFor, ast.While)):
                o = outer or child.lineno
                if depth + 1 > best[0]:
                    best = (depth + 1, o)
                walk(child, depth + 1, o)
            else:
                walk(child, depth, outer)
    walk(fn, 0, None)
    return best


def scan_file(path):
    out = []
    try:
        src = open(path, encoding="utf-8").read()
        tree = ast.parse(src)
    except (SyntaxError, UnicodeDecodeError, OSError) as e:
        return [(path, 0, "ERR", f"cannot parse: {e}")]
    skip = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if node.value is not None and any(isinstance(t, ast.Name) and t.id.isupper() for t in targets):
                skip.update(id(c) for c in ast.walk(node.value) if isinstance(c, ast.Constant))
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
            skip.add(id(node.value))  # docstrings / bare strings
    in_test = is_test_path(path)
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            names = node.type.id if isinstance(node.type, ast.Name) else None
            swallow = all(isinstance(b, ast.Pass) or (isinstance(b, ast.Expr) and isinstance(b.value, ast.Constant) and b.value.value is Ellipsis) for b in node.body)
            if node.type is None:
                out.append((path, node.lineno, "M03", "bare except (catches everything, including KeyboardInterrupt)"))
            elif names == "BaseException":
                out.append((path, node.lineno, "M03", "except BaseException"))
            elif swallow:
                out.append((path, node.lineno, "M03", "handler body is only pass/... (error swallowed)"))
        if isinstance(node, ast.Global):
            out.append((path, node.lineno, "M06", f"global statement: {', '.join(node.names)}"))
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            length = (node.end_lineno or node.lineno) - node.lineno + 1
            if length > LONG_FUNC:
                out.append((path, node.lineno, "M08", f"function '{node.name}' is {length} lines"))
            names = [a.arg for a in node.args.posonlyargs + node.args.args + node.args.kwonlyargs if a.arg not in ("self", "cls")]
            if len(names) > MANY_ARGS:
                out.append((path, node.lineno, "M08", f"function '{node.name}' has {len(names)} parameters"))
            defaults = list(node.args.defaults) + [d for d in node.args.kw_defaults if d is not None]
            flags = [d for d in defaults if isinstance(d, ast.Constant) and isinstance(d.value, bool)]
            if len(flags) >= 3:
                out.append((path, node.lineno, "M08", f"function '{node.name}' has {len(flags)} boolean flag parameters"))
            depth, where = loop_depth_report(node)
            if depth >= NEST_LIMIT:
                out.append((path, where, "M05", f"loops nested {depth} deep in '{node.name}'"))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("read", "readlines") and not node.args:
            out.append((path, node.lineno, "M05", f"whole-input .{node.func.attr}() (possible fixed-scale assumption)"))
        if isinstance(node, ast.Constant) and id(node) not in skip and not in_test:
            v = node.value
            if isinstance(v, (int, float)) and not isinstance(v, bool) and v not in ALLOWED_NUMBERS:
                out.append((path, getattr(node, "lineno", 0), "M01", f"hard-coded number {v}"))
            if isinstance(v, str) and (v.startswith(("http://", "https://")) or (len(v) > 2 and v[1:3] in (":\\", ":/"))):
                out.append((path, getattr(node, "lineno", 0), "M01", f"hard-coded URL/path {v[:40]}"))
    for i, line in enumerate(src.splitlines(), 1):
        low = line.lower()
        if "# todo" in low or "# fixme" in low or "# hack" in low:
            out.append((path, i, "NOTE", "marker comment: " + line.strip()[:50]))
    return out


def find_duplicates(files):
    seen = collections.defaultdict(list)
    for p in files:
        try:
            lines = [l.strip() for l in open(p, encoding="utf-8").read().splitlines()]
        except (OSError, UnicodeDecodeError):
            continue
        for i in range(len(lines) - DUP_MIN_LINES + 1):
            block = lines[i:i + DUP_MIN_LINES]
            if sum(1 for l in block if len(l) > 3 and not l.startswith("#")) < DUP_MIN_LINES:
                continue
            seen[hashlib.sha1("\n".join(block).encode()).hexdigest()].append((p, i + 1))
    dups = {k: v for k, v in seen.items() if len(v) > 1}
    covered = {loc for v in dups.values() for loc in v}
    out = []
    for locs in dups.values():
        if all((p, n - 1) in covered for p, n in locs):
            continue  # continuation of a region already reported at its first window
        p0, n0 = locs[0]
        run = 0
        while all((p, n + run) in covered for p, n in locs):
            run += 1
        where = ", ".join(f"{p}:{n}" for p, n in locs[:4])
        out.append((p0, n0, "M04", f"duplicated region of about {DUP_MIN_LINES + run - 1} lines in {len(locs)} places: {where}"))
    return out


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    files = list(iter_py(args[0]))
    findings = []
    for f in files:
        findings += scan_file(f)
    findings += find_duplicates(files)
    findings.sort(key=lambda x: (x[0], x[1]))
    if "--json" in sys.argv:
        print(json.dumps([dict(file=f, line=l, pattern=p, note=n) for f, l, p, n in findings], indent=1))
    else:
        for f, l, p, n in findings:
            print(f"{f}:{l}  [{p}]  {n}")
        print(f"\n{len(files)} files, {len(findings)} candidates:", dict(collections.Counter(p for _, _, p, _ in findings)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
