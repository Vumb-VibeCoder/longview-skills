#!/usr/bin/env python3
"""Validate the longview-skills repo and (optionally) rebuild dist/. Standard library only.
Usage: python tools/validate_repo.py [--build]
Checks every skill: frontmatter (name == folder, description < 1024 chars, status READY|PLANNED), English-only text,
cross-references to other skills resolve, every `scripts/x.py` and `templates/x` named in a SKILL.md exists in that
skill's folder, every Python file compiles. Exit code 1 if anything fails."""
import ast, glob, os, re, sys, zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOMAINS = ("core", "coding", "finance", "design", "ui")
NON_SKILL_NAMES = {"pip-audit", "pre-commit", "go-mod", "git-blame"}   # tool names that look like skill names
NON_SKILL_PREFIXES = ("color-", "space-", "font-", "radius-", "prefers-", "z-")   # CSS/token names in examples
VI = re.compile("[\u00e0-\u00e3\u00e8\u00ea\u00ec\u00ed\u00f2-\u00f5\u00f9\u00fa\u00fd\u0103\u0111\u0129\u0169\u01a1\u01b0\u1ea0-\u1ef9]", re.I)  # Vietnamese letters
errors, warns = [], []

def err(m): errors.append(m)

def skills():
    out = {}
    for d in DOMAINS:
        for f in sorted(glob.glob(os.path.join(ROOT, d, "*", "SKILL.md"))):
            out[os.path.basename(os.path.dirname(f))] = f
    return out

def frontmatter(text, path):
    parts = text.split("---")
    if not text.startswith("---") or len(parts) < 3:
        err(f"{path}: no frontmatter"); return {}
    fm = {}
    for line in parts[1].splitlines():
        m = re.match(r"\s*([\w-]+):\s*(.*)", line)
        if m: fm[m.group(1)] = m.group(2).strip()
    return fm

def main():
    sk = skills()
    for name, f in sk.items():
        rel = os.path.relpath(f, ROOT); text = open(f, encoding="utf-8").read(); fm = frontmatter(text, rel)
        domain = os.path.basename(os.path.dirname(os.path.dirname(f)))
        if fm.get("name") != name: err(f"{rel}: name '{fm.get('name')}' != folder '{name}'")
        d = fm.get("description", "")
        if not d: err(f"{rel}: missing description")
        elif len(d) >= 1024: err(f"{rel}: description is {len(d)} chars (limit 1023)")
        if fm.get("status") not in ("READY", "PLANNED"): err(f"{rel}: status must be READY or PLANNED")
        if fm.get("domain") not in (None, domain): err(f"{rel}: domain '{fm.get('domain')}' != folder '{domain}'")
        for ref in set(re.findall(r"`([a-z][a-z0-9]*(?:-[a-z0-9]+)+)`", text)):
            if ref not in sk and ref not in NON_SKILL_NAMES and not ref.startswith(NON_SKILL_PREFIXES) and not ref.endswith((".py", ".json", ".md")):
                err(f"{rel}: references unknown skill `{ref}`")
        sdir = os.path.dirname(f)
        for sub in set(re.findall(r"(?:scripts|templates)/[\w.\-]+\.\w+", text)):
            if not os.path.exists(os.path.join(sdir, sub)): err(f"{rel}: names `{sub}` but it does not exist in the skill folder")
    texts = [p for p in glob.glob(os.path.join(ROOT, "**", "*"), recursive=True)
             if p.endswith((".md", ".py", ".json")) and "dist" + os.sep not in p and "__pycache__" not in p]
    for p in texts:
        t = open(p, encoding="utf-8", errors="replace").read()
        if VI.search(t): err(f"{os.path.relpath(p, ROOT)}: contains Vietnamese text (repo must be English only)")
        if p.endswith(".py"):
            try: ast.parse(t)
            except SyntaxError as e: err(f"{os.path.relpath(p, ROOT)}: syntax error line {e.lineno}")
    # router coverage: every skill must be reachable from the routing table
    rt = os.path.join(ROOT, "core", "skill-router", "SKILL.md")
    if os.path.exists(rt):
        rtext = open(rt, encoding="utf-8").read()
        for name in sk:
            if name != "skill-router" and f"`{name}`" not in rtext:
                err(f"core/skill-router/SKILL.md: skill '{name}' is not in the routing table")
        import subprocess
        r = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "core", "skill-router", "scripts", "route.py"), "--test"], capture_output=True, text=True)
        if r.returncode != 0: err("routing regression failed:\n" + r.stdout)
    else:
        err("core/skill-router/SKILL.md missing")
    # cashflow regression: retirement example must match the independent calculation (checked by hand, 5%/12 monthly)
    cf = os.path.join(ROOT, "finance", "long-horizon-cashflow")
    if os.path.exists(cf):
        import subprocess, json as _j
        r = subprocess.run([sys.executable, "-I", os.path.join(cf, "scripts", "cashflow.py"), os.path.join(cf, "templates", "retirement.example.json"), "--json"], capture_output=True, text=True)
        try:
            rows = {x["scenario"]: x for x in _j.JSONDecoder().raw_decode(r.stdout)[0]}
            if rows["BASE"]["final_nominal"] != 153225.57 or rows["withdrawals indexed to 3%"]["first_negative_month"] != 250:
                err("cashflow.py retirement regression: numbers changed (expected 153225.57 and month 250)")
        except Exception as e:
            err(f"cashflow.py retirement example failed to run: {e}")
    print(f"{len(sk)} skills, {len(texts)} text files checked")
    if errors:
        print(f"FAIL: {len(errors)} problem(s)"); [print(" -", e) for e in errors]
    else:
        print("OK: all checks passed")
    if "--build" in sys.argv:
        if errors: print("not building dist/ while checks fail"); sys.exit(1)
        os.makedirs(os.path.join(ROOT, "dist"), exist_ok=True)
        for name, f in sk.items():
            base = os.path.dirname(f); zp = os.path.join(ROOT, "dist", name + ".zip")
            with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
                for dp, dn, fn in os.walk(base):
                    dn[:] = [x for x in dn if x != "__pycache__"]
                    for x in fn:
                        full = os.path.join(dp, x); z.write(full, os.path.join(name, os.path.relpath(full, base)))
        print(f"rebuilt {len(sk)} zips in dist/")
    sys.exit(1 if errors else 0)

if __name__ == "__main__": main()
