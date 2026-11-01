#!/usr/bin/env python3
"""Create a context-free copy of a project for the archaeology test.

Usage: python scripts/prepare_blind_copy.py <src_dir> <out_dir>
Removes what a stranger would NOT reliably have: git history, markdown/rst docs, ADRs,
CHANGELOG/TODO/NOTES files, .github. Keeps code, tests, config and in-code comments
(comments are part of the code). Prints what was removed so the test conditions can be
stated. Refuses to overwrite <out_dir>. Standard library only.
"""
import os, re, shutil, sys

DROP_DIRS = {".git", "docs", "doc", "adr", "adrs", "decisions", ".github", "node_modules", "venv", ".venv", "__pycache__", "dist", "build"}
DROP_FILE = re.compile(r"(?i)^(readme.*|changelog.*|history.*|todo.*|notes.*|contributing.*|architecture.*|design.*|.*\.(md|rst|adoc))$")


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, out = sys.argv[1], sys.argv[2]
    if os.path.exists(out):
        sys.exit(f"refusing to overwrite existing {out}")
    kept, dropped = 0, []
    for r, dirs, fs in os.walk(src):
        rel_r = os.path.relpath(r, src)
        for d in list(dirs):
            if d.lower() in DROP_DIRS:
                dropped.append(os.path.normpath(os.path.join(rel_r, d)) + "/"); dirs.remove(d)
        for f in fs:
            rel = os.path.normpath(os.path.join(rel_r, f))
            if DROP_FILE.match(f):
                dropped.append(rel); continue
            dst = os.path.join(out, rel)
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(os.path.join(r, f), dst); kept += 1
    print(f"kept {kept} files in {out}; removed {len(dropped)} items (state these as the test conditions):")
    for d in sorted(dropped)[:50]:
        print("  -", d)


if __name__ == "__main__":
    main()
