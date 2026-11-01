#!/usr/bin/env python3
"""Measure module coupling for Python and JS/TS: fan-in, fan-out, instability, cycles.

Usage: python scripts/module_graph.py <src_dir> [--depth N] [--json]
A module = the first N directory components under <src_dir> (default 1); files directly
in <src_dir> form the module "(root)". Only imports that resolve to ANOTHER module inside
<src_dir> are counted. Instability I = fan_out / (fan_in + fan_out): 0 stable, 1 volatile.
Standard library only. It measures structure; judging whether boundaries are RIGHT needs
the skill's reading procedure.
"""
import ast, collections, json, os, re, sys

SKIP = {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "dist", "tests", "test"}
JS_EXT = (".js", ".jsx", ".ts", ".tsx", ".mjs")
JS_IMPORT = re.compile(r"""(?:from\s+|require\(\s*|import\(\s*|import\s+)['"](\.{1,2}/[^'"]*)['"]""")


def module_of(parts, depth):
    dirs = parts[:-1]
    return "(root)" if not dirs else "/".join(dirs[:depth])


def py_targets(path, parts, rootname):
    try:
        tree = ast.parse(open(path, errors="ignore").read())
    except SyntaxError:
        return []
    out = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                p = a.name.split(".")
                out.append(p[1:] if p[0] == rootname else p)
        elif isinstance(n, ast.ImportFrom):
            if n.level:
                base = parts[:-1][: max(len(parts) - 1 - (n.level - 1), 0)]
                out.append(base + (n.module.split(".") if n.module else []))
            elif n.module:
                p = n.module.split(".")
                p = p[1:] if p[0] == rootname else p
                out.append(p + [a.name for a in n.names][:1] if len(p) < 2 else p)
    return out


def js_targets(path, parts):
    txt = open(path, errors="ignore").read()
    base = "/".join(parts[:-1])
    return [os.path.normpath(os.path.join(base, m.group(1))).replace("\\", "/").split("/")
            for m in JS_IMPORT.finditer(txt)]


def cycles_of(edges):
    g = collections.defaultdict(set)
    for a, b in edges:
        g[a].add(b)
    idx, low, on, st, res, c = {}, {}, set(), [], [], [0]
    sys.setrecursionlimit(10000)

    def visit(v):
        idx[v] = low[v] = c[0]; c[0] += 1; st.append(v); on.add(v)
        for w in g[v]:
            if w not in idx:
                visit(w); low[v] = min(low[v], low[w])
            elif w in on:
                low[v] = min(low[v], idx[w])
        if low[v] == idx[v]:
            comp = []
            while True:
                w = st.pop(); on.discard(w); comp.append(w)
                if w == v:
                    break
            if len(comp) > 1:
                res.append(sorted(comp))

    for v in list(g):
        if v not in idx:
            visit(v)
    return res


def main():
    argv = sys.argv[1:]
    depth = 1
    if "--depth" in argv:
        i = argv.index("--depth"); depth = int(argv[i + 1]); del argv[i:i + 2]
    pos = [a for a in argv if not a.startswith("--")]
    if not pos:
        sys.exit(__doc__)
    root = os.path.abspath(pos[0]); rootname = os.path.basename(root)
    files = []
    for r, dirs, fs in os.walk(root):
        dirs[:] = [d for d in dirs if d not in SKIP]
        for f in fs:
            if f.endswith(".py") or f.endswith(JS_EXT):
                rel = os.path.relpath(os.path.join(r, f), root).replace("\\", "/")
                files.append((os.path.join(r, f), rel.split("/")))
    tops = {p[0] for _, p in files if len(p) > 1}
    root_stems = {os.path.splitext(p[0])[0] for _, p in files if len(p) == 1}
    edges, counts = set(), collections.Counter()
    for path, parts in files:
        src = module_of(parts, depth)
        raw = py_targets(path, parts, rootname) if path.endswith(".py") else js_targets(path, parts)
        for t in raw:
            if not t:
                continue
            if t[0] in tops:
                tgt = module_of(t + ["_"], depth)   # "_" stands for the imported symbol/file
            elif t[0] in root_stems:
                tgt = "(root)"
            else:
                continue
            if tgt != src:
                edges.add((src, tgt)); counts[(src, tgt)] += 1
    mods = sorted({module_of(p, depth) for _, p in files})
    fo = collections.Counter(a for a, _ in edges); fi = collections.Counter(b for _, b in edges)
    rows = [{"module": m, "fan_in": fi[m], "fan_out": fo[m],
             "instability": round(fo[m] / (fo[m] + fi[m]), 2) if fo[m] + fi[m] else None} for m in mods]
    cyc = cycles_of(edges)
    out = {"files": len(files), "modules": rows,
           "edges": sorted(f"{a} -> {b} (x{counts[(a, b)]})" for a, b in edges), "cycles": cyc}
    if "--json" in sys.argv:
        print(json.dumps(out, indent=2)); return
    print(f"files: {len(files)} | modules: {len(mods)} | cross-module edges: {len(edges)} | cycles: {len(cyc)}")
    for r in sorted(rows, key=lambda r: -(r["fan_in"] + r["fan_out"])):
        print(f"  {r['module']:<28} in={r['fan_in']:<3} out={r['fan_out']:<3} I={r['instability']}")
    for e in out["edges"]:
        print("  edge:", e)
    for c in cyc:
        print("  CYCLE:", " <-> ".join(c))


if __name__ == "__main__":
    main()
