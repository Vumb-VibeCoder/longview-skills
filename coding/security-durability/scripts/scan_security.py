#!/usr/bin/env python3
"""Pattern scan for common security mistakes. Standard library only.
Usage: python scan_security.py PATH [--json]
Exit codes: 0 no findings, 1 findings, 2 bad input.
This is a first pass, not a penetration test: it finds known-bad patterns,
not logic flaws. Secret values are masked in the output."""
import json, os, re, sys

SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", ".tox"}
EXTS = {".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".java", ".rb", ".php", ".cs", ".sh", ".yml", ".yaml",
        ".json", ".toml", ".ini", ".cfg", ".env", ".tf", ".properties"}
MAX_BYTES = 1_000_000

RULES = [
    ("SEC01", "high", "hard-coded secret or key",
     re.compile(r"(?i)[\w-]*(?:api[_-]?key|secret|token|passwd|password|private[_-]?key)[\w-]*[\"']?\s*[:=]\s*[\"'](?!https?://)[^\"'\s]{8,}[\"']")),
    ("SEC01", "high", "cloud or VCS credential",
     re.compile(r"\bAKIA[0-9A-Z]{16}\b|\bgh[pousr]_[A-Za-z0-9]{36,}\b|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("SEC02", "high", "TLS certificate check switched off",
     re.compile(r"verify\s*=\s*False|rejectUnauthorized\s*:\s*false|InsecureSkipVerify\s*:\s*true|CURLOPT_SSL_VERIFYPEER\s*,\s*(?:false|0)")),
    ("SEC03", "high", "shell command built from a string",
     re.compile(r"shell\s*=\s*True|\bos\.system\(|\bRuntime\.getRuntime\(\)\.exec\(")),
    ("SEC04", "high", "SQL built by string formatting",
     re.compile(r"(?i)\b(?:execute|query|raw)\(\s*(?:f[\"']|[\"'][^\"']*[\"']\s*(?:%|\+|\.format\())")),
    ("SEC05", "high", "unsafe deserialization",
     re.compile(r"\bpickle\.loads?\(|\byaml\.load\((?![^)]*Loader)|\bmarshal\.loads?\(")),
    ("SEC06", "medium", "eval or exec on dynamic input",
     re.compile(r"(?<![\w.])(?:eval|exec)\(")),
    ("SEC07", "medium", "weak hash (not for passwords or signatures)",
     re.compile(r"\bhashlib\.(?:md5|sha1)\(|\bMD5\.Create\(|createHash\(\s*[\"'](?:md5|sha1)[\"']")),
    ("SEC08", "medium", "debug mode on",
     re.compile(r"\bdebug\s*=\s*True\b|\bDEBUG\s*=\s*True\b")),
    ("SEC09", "medium", "world-writable permissions or wildcard CORS",
     re.compile(r"chmod\(?[^\n]*\b0?o?777\b|Access-Control-Allow-Origin[\"']?\s*[:,]\s*[\"']?\*")),
    ("SEC10", "medium", "unencrypted http:// URL used for a request or as an endpoint",
     re.compile(r"(?i)(?:\b(?:requests|httpx|session|client)\.\w+\(|\burlopen\(|\bfetch\(|\baxios(?:\.\w+)?\(|\bhttp\.get\(|\b\w*(?:url|endpoint|host|base)\w*\s*[:=])\s*[f\"']?\s*[\"']http://(?!localhost\b|127\.|0\.0\.0\.0|\[::1\]|[\w.-]*\.(?:test|example|invalid)\b|www\.w3\.org|schemas\.)")),
]

def mask(line, rule_id, m):
    """Hide secret values so the report itself does not leak them."""
    s = line.strip()
    if rule_id == "SEC01":
        s = s.replace(m.group(0), m.group(0)[:4] + "***") if m.group(0).startswith(("AKIA", "gh", "-----")) \
            else re.sub(r"([\"'])[^\"']{4,}\1", '"***"', s)
    return s[:140]

def files(root):
    if os.path.isfile(root):
        yield root; return
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for f in fn:
            if os.path.splitext(f)[1].lower() in EXTS or f.startswith(".env"):
                yield os.path.join(dp, f)

def scan(root):
    found = []
    for p in files(root):
        try:
            if os.path.getsize(p) > MAX_BYTES: continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                for n, line in enumerate(fh, 1):
                    if "nosec" in line or "scan-ignore" in line: continue
                    for rid, sev, what, rx in RULES:
                        m = rx.search(line)
                        if m:
                            found.append({"file": p, "line": n, "id": rid, "severity": sev, "what": what, "text": mask(line, rid, m)})
                            break
        except OSError:
            continue
    return found

def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); return 2
    if not os.path.exists(args[0]):
        print(f"ERROR: path not found: {args[0]}", file=sys.stderr); return 2
    res = scan(args[0])
    if "--json" in sys.argv:
        print(json.dumps(res, indent=2))
    else:
        for r in sorted(res, key=lambda r: (r["severity"] != "high", r["file"], r["line"])):
            print(f"{r['severity'].upper():6} {r['id']} {r['file']}:{r['line']}  {r['what']}\n         {r['text']}")
        high = sum(r["severity"] == "high" for r in res)
        print(f"{len(res)} finding(s), {high} high. Pattern scan only: not a substitute for review or testing.")
    return 1 if res else 0

if __name__ == "__main__":
    sys.exit(main())
