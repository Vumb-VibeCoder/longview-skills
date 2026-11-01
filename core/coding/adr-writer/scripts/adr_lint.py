#!/usr/bin/env python3
"""Lint a directory of ADRs (files named NNNN-slug.md).

Usage: python scripts/adr_lint.py <adr_dir>
Checks: filename pattern and unique, gapless numbering; title "# ADR-NNNN:" matches filename;
Status valid; Date valid; required sections non-empty (Context, Decision, Alternatives considered,
Consequences, Revisit when, Related); at least 2 numbered alternatives; "Superseded by" targets
exist; a Superseded ADR is referenced back by its successor ("Supersedes:"); Door=ONE-WAY needs a
concrete Revisit-when (not "n/a"/"none"); Accepted ADRs must not contain TODO/TBD/<...> placeholders.
Exit 1 on any finding. Standard library only.
"""
import datetime, os, re, sys

SECTIONS = ["Context", "Decision", "Alternatives considered", "Consequences", "Revisit when", "Related"]
STATUS = re.compile(r"^(Proposed|Accepted|Rejected|Deprecated|Superseded by ADR-(\d{4}))$")
EMPTY = {"", "n/a", "na", "none", "tbd", "todo", "-"}


def section(text, name):
    m = re.search(rf"^## {re.escape(name)}\s*\n(.*?)(?=^## |\Z)", text, re.S | re.M)
    return m.group(1).strip() if m else None


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    d = sys.argv[1]
    files = sorted(f for f in os.listdir(d) if f.endswith(".md"))
    problems, nums, info = [], {}, {}

    def bad(f, msg):
        problems.append(f"{f}: {msg}")

    for f in files:
        m = re.match(r"^(\d{4})-[a-z0-9][a-z0-9-]*\.md$", f)
        if not m:
            bad(f, "filename must be NNNN-kebab-slug.md"); continue
        n = int(m.group(1))
        if n in nums:
            bad(f, f"duplicate number with {nums[n]}")
        nums[n] = f
        t = open(os.path.join(d, f), encoding="utf-8").read()
        title = re.search(r"^# ADR-(\d{4}): (\S.*)$", t, re.M)
        if not title or int(title.group(1)) != n:
            bad(f, "first heading must be '# ADR-NNNN: title' matching the filename")
        st = re.search(r"^- Status: (.+)$", t, re.M)
        status = st.group(1).strip() if st else ""
        sm = STATUS.match(status)
        if not sm:
            bad(f, f"invalid Status '{status}'")
        dt = re.search(r"^- Date: (\S+)$", t, re.M)
        try:
            datetime.date.fromisoformat(dt.group(1))
        except Exception:
            bad(f, "Date must be YYYY-MM-DD")
        door = re.search(r"^- Door: (\S+)", t, re.M)
        if not door or door.group(1) not in ("CHEAP", "COSTLY", "ONE-WAY"):
            bad(f, "Door must be CHEAP | COSTLY | ONE-WAY")
        body = {}
        for s in SECTIONS:
            body[s] = section(t, s)
            if body[s] is None or body[s].lower() in EMPTY:
                bad(f, f"section '{s}' missing or empty")
        alts = body["Alternatives considered"] or ""
        if len(re.findall(r"^\s*\d+\.", alts, re.M)) < 2:
            bad(f, "need at least 2 numbered alternatives (include 'do nothing / baseline')")
        if door and door.group(1) == "ONE-WAY" and (body["Revisit when"] or "").lower() in EMPTY:
            bad(f, "ONE-WAY decision needs a concrete 'Revisit when'")
        if status == "Accepted" and re.search(r"\b(TODO|TBD)\b|<[^>\n]+>", t.split("## Context", 1)[-1]):
            bad(f, "Accepted ADR still contains placeholders (TODO/TBD/<...>)")
        info[n] = (status, sm.group(2) if sm else None, t)
    if nums:
        missing = [i for i in range(min(nums), max(nums) + 1) if i not in nums]
        if missing:
            problems.append(f"numbering gap: {missing}")
    for n, (status, succ, t) in info.items():
        if succ:
            s = int(succ)
            if s not in nums:
                problems.append(f"{nums[n]}: superseded by ADR-{succ} which does not exist")
            else:
                line = re.search(r"Supersedes:.*", info[s][2])
                if not line or f"ADR-{n:04d}" not in line.group(0):
                    problems.append(f"{nums[s]}: should list ADR-{n:04d} after 'Supersedes:' in Related")
    for p in problems:
        print("PROBLEM", p)
    print(f"{len(files)} files, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
