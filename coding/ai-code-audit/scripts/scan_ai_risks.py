#!/usr/bin/env python3
"""Scan Python code for mistakes that AI-written code makes often. Standard library only.

Usage: python scripts/scan_ai_risks.py <file_or_dir> [--json]
Exit codes: 0 no candidates, 1 candidates found, 2 bad input.
Output lines are CANDIDATES. Confirm each by reading the code (see SKILL.md).

Detects:
  A01  import that is not stdlib, not local and not declared in a manifest (requirements*.txt,
       pyproject.toml, setup.py, setup.cfg, Pipfile). Marked "not installed" when the module also
       cannot be found in this environment (possible invented package).
  A02  attribute or `from X import name` that does not exist on a stdlib module (possible invented API).
       May be platform- or version-specific: the scan checks against the interpreter that runs it.
  A03  placeholder code: body that is only pass / ... / NotImplementedError, template secrets
       ("YOUR_API_KEY"), elision comments ("rest of the code", "same as before").
  A04  test that cannot fail: no assertion, `assert True`, `assert x == x`, skipped or xfail test,
       assertion wrapped in `except AssertionError: pass`.
  A05  abstract base class with at most one subclass in the scanned files (premature abstraction, M10).
  A06  unused import.
"""
import ast, collections, importlib, importlib.util, json, os, re, sys

SKIP_DIRS = {".git", "node_modules", "venv", ".venv", "__pycache__", "build", "dist", ".tox", "site-packages"}
MANIFESTS = ("requirements", "pyproject.toml", "setup.py", "setup.cfg", "Pipfile")
# import name -> distribution name, where they differ
ALIASES = {"yaml": "pyyaml", "pil": "pillow", "cv2": "opencv-python", "sklearn": "scikit-learn", "bs4": "beautifulsoup4",
           "dateutil": "python-dateutil", "dotenv": "python-dotenv", "jwt": "pyjwt", "serial": "pyserial",
           "attr": "attrs", "git": "gitpython", "magic": "python-magic", "google": "google-api-python-client",
           "skimage": "scikit-image", "crypto": "pycryptodome", "openssl": "pyopenssl"}
NO_IMPORT = {"antigravity", "this", "idlelib", "turtledemo", "lib2to3", "tkinter", "turtle", "pydoc_data", "__main__", "__phello__"}
PLACEHOLDER_STR = re.compile(r"(?i)^(your[_ -]?(api[_ -]?)?(key|token|secret|password)[\w -]*|<your[^>]*>|changeme|lorem ipsum.*|xxx+|replace[_ -]?me|insert[_ -]?\w+[_ -]?here)$")
ELISION = re.compile(r"(?i)#\s*(\.\.\.|\u2026)|rest of (the |your )?(code|file|function|implementation|class)|(existing|previous|original) (code|implementation)\b|same as (above|before)|implement (this|me|later)|add (your )?(logic|code|implementation) here")
STDLIB = set(getattr(sys, "stdlib_module_names", ())) | set(sys.builtin_module_names)


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


def norm(n):
    return re.sub(r"[-_.]+", "_", n.strip().lower())


def read_declared(roots):
    """Return (set of declared distribution names, manifest found?)."""
    declared, found, seen = set(), False, set()
    for r in roots:
        r = os.path.abspath(r)
        if r in seen or not os.path.isdir(r):
            continue
        seen.add(r)
        for f in sorted(os.listdir(r)):
            if not f.startswith(MANIFESTS):
                continue
            found = True
            try:
                text = open(os.path.join(r, f), encoding="utf-8", errors="replace").read()
            except OSError:
                continue
            for tok in re.findall(r"(?<![\w.-])([A-Za-z][A-Za-z0-9._-]*)", text):
                declared.add(norm(tok))
    return declared, found


def local_names(files, root):
    names = {os.path.splitext(os.path.basename(f))[0] for f in files}
    base = root if os.path.isdir(root) else (os.path.dirname(root) or ".")
    for dp, dn, fn in os.walk(base):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        names.update(dn)
        names.update(x[:-3] for x in fn if x.endswith(".py"))
    return names


def parse(path):
    try:
        text = open(path, encoding="utf-8").read()
        return text, ast.parse(text, filename=path)
    except (OSError, UnicodeDecodeError, SyntaxError):
        return None, None


def check_imports(path, tree, ctx):
    out = []
    for node in ast.walk(tree):
        mods = []
        if isinstance(node, ast.Import):
            mods = [(a.name, node.lineno) for a in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            mods = [(node.module, node.lineno)]
        for name, line in mods:
            t = name.split(".")[0]
            if t in STDLIB or t in ctx["local"] or t == "__future__":
                continue
            dist = ALIASES.get(t.lower(), t)
            if norm(t) in ctx["declared"] or norm(dist) in ctx["declared"]:
                continue
            try:
                installed = importlib.util.find_spec(t) is not None
            except (ImportError, ValueError):
                installed = False
            if not ctx["manifest"]:
                note = f"import `{t}` is not stdlib or local, and no dependency manifest was found, so it cannot be checked"
                if not installed:
                    note += "; it is also not installed here (possible invented package)"
            elif installed:
                note = f"import `{t}` is installed here but not declared in the manifest (works on this machine only)"
            else:
                note = f"import `{t}` is not declared in the manifest and not installed here (possible invented package)"
            out.append((path, line, "A01", note))
    return out


def stdlib_module(name):
    if name in NO_IMPORT or name.startswith("_") or name not in STDLIB:
        return None
    try:
        return importlib.import_module(name)
    except BaseException:
        return None


def check_stdlib_attrs(path, tree):
    out, aliases = [], {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if "." not in a.name:
                    aliases[a.asname or a.name] = a.name
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module and "." not in node.module:
            mod = stdlib_module(node.module)
            if mod is None:
                continue
            for a in node.names:
                if a.name == "*" or hasattr(mod, a.name):
                    continue
                try:
                    importlib.import_module(f"{node.module}.{a.name}")
                except BaseException:
                    out.append((path, node.lineno, "A02", f"`from {node.module} import {a.name}`: no such name in the standard library module (possible invented API; check platform and version)"))
        elif isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name) and node.value.id in aliases:
            real = aliases[node.value.id]
            mod = stdlib_module(real)
            if mod is not None and not hasattr(mod, node.attr):
                try:
                    importlib.import_module(f"{real}.{node.attr}")
                except BaseException:
                    out.append((path, node.lineno, "A02", f"`{node.value.id}.{node.attr}`: module `{real}` has no such attribute (possible invented API; check platform and version)"))
    return out


def is_abstract_context(fn, parents):
    for d in fn.decorator_list:
        n = ast.unparse(d)
        if "abstractmethod" in n or "overload" in n:
            return True
    cls = parents.get(fn)
    if isinstance(cls, ast.ClassDef):
        for b in cls.bases:
            if re.search(r"ABC|Protocol|Interface", ast.unparse(b)):
                return True
    return False


def body_is_placeholder(fn):
    body = list(fn.body)
    if body and isinstance(body[0], ast.Expr) and isinstance(getattr(body[0], "value", None), ast.Constant) and isinstance(body[0].value.value, str):
        body = body[1:]
    if not body:
        return "has only a docstring"
    if len(body) == 1:
        s = body[0]
        if isinstance(s, ast.Pass):
            return "body is only `pass`"
        if isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant) and s.value.value is Ellipsis:
            return "body is only `...`"
        if isinstance(s, ast.Raise) and s.exc is not None and "NotImplementedError" in ast.unparse(s.exc):
            return "body only raises NotImplementedError"
    return None


def check_placeholders(path, text, tree):
    out, parents = [], {}
    for p in ast.walk(tree):
        for c in ast.iter_child_nodes(p):
            parents[c] = p
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            why = body_is_placeholder(node)
            if why and not is_abstract_context(node, parents) and not node.name.startswith("__"):
                out.append((path, node.lineno, "A03", f"function `{node.name}` {why}: a stub that callers may treat as working"))
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and 3 <= len(node.value) <= 60:
            if PLACEHOLDER_STR.match(node.value.strip()):
                out.append((path, node.lineno, "A03", f"template value left in code: {node.value!r}"))
    for i, line in enumerate(text.splitlines(), 1):
        if "#" in line and ELISION.search(line):
            out.append((path, i, "A03", "comment stands in for code that is missing (typical of elided AI output): " + line.strip()[:70]))
    return out


def has_assert(fn):
    for n in ast.walk(fn):
        if isinstance(n, ast.Assert):
            return True
        if isinstance(n, ast.Call) and re.search(r"(^|\.)assert\w*$|raises$|warns$|\.fail$", ast.unparse(n.func)):
            return True
        if isinstance(n, ast.With):
            for it in n.items:
                if re.search(r"raises|warns|assertRaises|assertWarns", ast.unparse(it.context_expr)):
                    return True
    return False


def check_tests(path, tree):
    out = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) or not node.name.startswith("test"):
            continue
        decos = " ".join(ast.unparse(d) for d in node.decorator_list)
        skipped = bool(re.search(r"skip|xfail", decos)) or any(
            isinstance(n, ast.Call) and re.search(r"(pytest|self)\.(skip|xfail)", ast.unparse(n.func)) for n in ast.walk(node))
        if skipped:
            out.append((path, node.lineno, "A04", f"test `{node.name}` is skipped or expected to fail: it protects nothing"))
        if not has_assert(node):
            out.append((path, node.lineno, "A04", f"test `{node.name}` has no assertion: it passes as long as nothing crashes"))
        for n in ast.walk(node):
            if isinstance(n, ast.Assert):
                t = n.test
                if isinstance(t, ast.Constant) and t.value:
                    out.append((path, n.lineno, "A04", "assertion of a constant truth value can never fail"))
                elif isinstance(t, ast.Compare) and len(t.ops) == 1 and isinstance(t.ops[0], (ast.Eq, ast.Is)) and ast.dump(t.left) == ast.dump(t.comparators[0]):
                    out.append((path, n.lineno, "A04", "assertion compares an expression with itself: it can never fail"))
            if isinstance(n, ast.Call) and ast.unparse(n.func).endswith(("assertTrue", "assertFalse")) and n.args:
                a = n.args[0]
                if isinstance(a, ast.Constant) and bool(a.value) == ast.unparse(n.func).endswith("assertTrue"):
                    out.append((path, n.lineno, "A04", "assertTrue/assertFalse on a constant can never fail"))
            if isinstance(n, ast.Try):
                for h in n.handlers:
                    if h.type is not None and "AssertionError" in ast.unparse(h.type) and all(isinstance(s, ast.Pass) for s in h.body):
                        out.append((path, h.lineno, "A04", "AssertionError is caught and ignored: failures are hidden"))
    return out


def collect_classes(path, tree, abstract, subclasses):
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b).split(".")[-1] for b in node.bases]
            abs_methods = any(
                isinstance(m, (ast.FunctionDef, ast.AsyncFunctionDef)) and any("abstractmethod" in ast.unparse(d) for d in m.decorator_list)
                for m in node.body)
            if any(b in ("ABC", "ABCMeta") for b in bases) or abs_methods:
                abstract[node.name] = (path, node.lineno)
            for b in bases:
                subclasses[b].append(node.name)


def check_unused_imports(path, text, tree):
    if os.path.basename(path) == "__init__.py" or "__all__" in text:
        return []
    imported = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                imported[(a.asname or a.name).split(".")[0]] = node.lineno
        elif isinstance(node, ast.ImportFrom) and node.module != "__future__":
            for a in node.names:
                if a.name != "*":
                    imported[a.asname or a.name] = node.lineno
    used = {n.id for n in ast.walk(tree) if isinstance(n, ast.Name)}
    strings = " ".join(c.value for c in ast.walk(tree) if isinstance(c, ast.Constant) and isinstance(c.value, str))
    used |= set(re.findall(r"[A-Za-z_]\w*", strings))  # names used only inside string annotations
    lines = text.splitlines()
    return [(path, line, "A06", f"`{name}` is imported and never used")
            for name, line in imported.items() if name not in used and "noqa" not in lines[line - 1]]


def scan(target):
    files = list(iter_py(target))
    base = os.path.abspath(target if os.path.isdir(target) else (os.path.dirname(target) or "."))
    declared, found = read_declared([base, os.path.dirname(base), os.path.dirname(os.path.dirname(base))])
    ctx = {"local": local_names(files, target), "declared": declared, "manifest": found}
    findings, abstract, subclasses = [], {}, collections.defaultdict(list)
    for f in files:
        text, tree = parse(f)
        if tree is None:
            continue
        findings += check_imports(f, tree, ctx)
        findings += check_stdlib_attrs(f, tree)
        findings += check_placeholders(f, text, tree)
        findings += check_unused_imports(f, text, tree)
        if is_test_path(f):
            findings += check_tests(f, tree)
        collect_classes(f, tree, abstract, subclasses)
    for name, (p, line) in abstract.items():
        n = len(subclasses.get(name, []))
        if n <= 1:
            findings.append((p, line, "A05", f"abstract class `{name}` has {n} subclass(es) in the scanned files: an interface with one implementation (M10)"))
    findings.sort(key=lambda x: (x[0], x[1], x[2]))
    return files, findings


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        return 2
    if not os.path.exists(args[0]):
        print(f"error: path not found: {args[0]}", file=sys.stderr)
        return 2
    files, findings = scan(args[0])
    if "--json" in sys.argv:
        print(json.dumps([dict(file=f, line=l, pattern=p, note=n) for f, l, p, n in findings], indent=1))
    else:
        for f, l, p, n in findings:
            print(f"{f}:{l}  [{p}]  {n}")
        print(f"\n{len(files)} files, {len(findings)} candidates:", dict(collections.Counter(p for _, _, p, _ in findings)))
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
