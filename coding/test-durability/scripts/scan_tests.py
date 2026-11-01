#!/usr/bin/env python3
"""Find test-suite habits that make tests rot or lie over the years. Standard library only.
Usage: python scan_tests.py PATH [--json]
Exit codes: 0 no findings, 1 findings, 2 bad input.
Pattern based: it flags habits, it does not run your tests or measure coverage."""
import ast, json, os, re, sys

SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", ".tox"}
TEST_NAME = re.compile(r"(^test_.*\.py$|.*_test\.(py|go)$|.*\.(test|spec)\.(js|jsx|ts|tsx)$)")
TEST_DIRS = {"test", "tests", "__tests__", "spec"}
CODE_EXT = {".py", ".js", ".jsx", ".ts", ".tsx", ".go"}

LINE_RULES = [
    ("TST02", "medium", "fixed sleep (flaky, slow)", re.compile(r"\btime\.sleep\(|\bThread\.sleep\(|\bsetTimeout\(|\btime\.Sleep\(")),
    ("TST03", "high", "real network call", re.compile(r"\brequests\.(?:get|post|put|delete)\(|\burlopen\(|\bfetch\(\s*[\"'`]https?://|\bhttp\.Get\(")),
    ("TST04", "medium", "depends on the real clock", re.compile(r"\bdatetime\.(?:now|today|utcnow)\(|\btime\.time\(\)|\bDate\.now\(\)|\bnew Date\(\)|\btime\.Now\(\)")),
    ("TST04", "medium", "hard-coded calendar date (rots as time passes)", re.compile(r"[\"'`]20[12]\d-\d\d-\d\d")),
    ("TST05", "medium", "skipped or disabled test", re.compile(r"@pytest\.mark\.(?:skip|xfail)|@unittest\.(?:skip|expectedFailure)|\b(?:it|test|describe)\.skip\(|\bxit\(|\bxdescribe\(|\bt\.Skip\(")),
    ("TST07", "high", "assertion that can never fail", re.compile(r"\bassert True\b|assertTrue\(\s*True\s*\)|expect\(\s*true\s*\)\.toBe\(\s*true\s*\)")),
    ("TST09", "low", "asserts on a private member (ties the test to the implementation)", re.compile(r"\bassert\w*\(?[^\n]*(?<!self)\.\_[a-zA-Z]\w*|expect\([^\n]*(?<!self)\._[a-zA-Z]\w*")),
]
ASSERT_WORDS = re.compile(r"\bassert|\.assert\w*|\bexpect\(|\bt\.(?:Error|Fatal)|pytest\.raises|assertRaises|should\b")
MOCK_WORDS = re.compile(r"\bMock\(|MagicMock|mock\.patch|@patch|jest\.mock|jest\.fn|sinon\.stub|\.mockReturnValue|gomock")

def is_test_file(path):
    name = os.path.basename(path)
    parts = set(os.path.normpath(path).split(os.sep)[:-1])
    return bool(TEST_NAME.match(name)) or (bool(parts & TEST_DIRS) and os.path.splitext(name)[1] in CODE_EXT)

def walk(root):
    if os.path.isfile(root):
        yield root; return
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if os.path.splitext(f)[1] in CODE_EXT:
                yield os.path.join(dp, f)

def python_no_assert(path, src):
    """Test functions with no assertion at all: they only prove the code does not crash."""
    out = []
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return out
    funcs = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    # helpers that contain an assertion: a test that calls one of them is not assertion-free
    helpers = {n.name for n in funcs if not n.name.startswith("test") and ASSERT_WORDS.search(ast.get_source_segment(src, n) or "")}
    for node in funcs:
        if node.name.startswith("test"):
            seg = ast.get_source_segment(src, node) or ""
            calls_helper = any(re.search(r"\b%s\(" % re.escape(h), seg) for h in helpers)
            if not ASSERT_WORDS.search(seg) and not calls_helper:
                out.append({"file": path, "line": node.lineno, "id": "TST01", "severity": "high",
                            "what": "test has no assertion", "text": node.name})
    return out

def scan(root):
    found, tests, sources = [], 0, 0
    for p in walk(root):
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                src = fh.read()
        except OSError:
            continue
        if not is_test_file(p):
            sources += 1; continue
        tests += 1
        if p.endswith(".py"):
            found += python_no_assert(p, src)
        for n, line in enumerate(src.split("\n"), 1):
            for rid, sev, what, rx in LINE_RULES:
                if rx.search(line):
                    found.append({"file": p, "line": n, "id": rid, "severity": sev, "what": what, "text": line.strip()[:140]})
                    break
        if re.search(r"\brandom\.|Math\.random\(|rand\.", src) and not re.search(r"seed", src, re.I):
            found.append({"file": p, "line": 1, "id": "TST06", "severity": "medium",
                          "what": "uses randomness with no seed (failures cannot be reproduced)", "text": ""})
        mocks, asserts = len(MOCK_WORDS.findall(src)), len(ASSERT_WORDS.findall(src))
        if mocks >= 3 and mocks > asserts:
            found.append({"file": p, "line": 1, "id": "TST08", "severity": "medium",
                          "what": f"more mocks ({mocks}) than assertions ({asserts}): may test the mocks, not the code", "text": ""})
    return found, tests, sources

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    if not os.path.exists(args[0]):
        print(f"ERROR: path not found: {args[0]}", file=sys.stderr); return 2
    found, tests, sources = scan(args[0])
    if "--json" in sys.argv:
        print(json.dumps({"test_files": tests, "other_code_files": sources, "findings": found}, indent=2))
    else:
        order = {"high": 0, "medium": 1, "low": 2}
        for r in sorted(found, key=lambda r: (order[r["severity"]], r["file"], r["line"])):
            print(f"{r['severity'].upper():6} {r['id']} {r['file']}:{r['line']}  {r['what']}" + (f"\n         {r['text']}" if r["text"] else ""))
        print(f"{tests} test file(s), {sources} other code file(s), {len(found)} finding(s).")
        if tests == 0:
            print("No test files found: the suite does not exist yet, or lives under a name this scan does not recognise.")
    return 1 if found else 0

if __name__ == "__main__":
    sys.exit(main())
