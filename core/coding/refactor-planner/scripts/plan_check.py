#!/usr/bin/env python3
"""Validate a refactoring plan (JSON) and print a safe execution order.

Usage: python scripts/plan_check.py <plan.json>
Plan = list of steps. Step fields:
  id, goal, type (CHARACTERIZE | SEAM | MOVE | REPLACE | DELETE | CLEANUP),
  depends_on [ids], hours (number), verify (how to prove the step is done and nothing broke),
  rollback (how to undo), behavior_change (true/false)
  optional: tests_exist (true if behaviour is already covered by trustworthy tests), debt_ids [ids]
Rules checked:
  - fields present; ids unique; depends_on exist; no cycles
  - hours <= 16 per step (larger steps must be split)
  - behavior_change must be false (refactoring never mixes with behaviour change)
  - MOVE / REPLACE / DELETE need a CHARACTERIZE step among their (transitive) dependencies, or tests_exist=true
  - REPLACE and DELETE need a SEAM or MOVE or CHARACTERIZE earlier in their chain (never first)
Prints the order (dependencies first; ties by smaller hours), total hours and the critical path.
Exit 1 on any problem. Standard library only.
"""
import json, sys

TYPES = {"CHARACTERIZE", "SEAM", "MOVE", "REPLACE", "DELETE", "CLEANUP"}
NEED_TESTS = {"MOVE", "REPLACE", "DELETE"}
REQ = ["id", "goal", "type", "depends_on", "hours", "verify", "rollback", "behavior_change"]


def main():
    if len(sys.argv) < 2:
        print(__doc__); return 2
    try:
        steps = json.load(open(sys.argv[1], encoding="utf-8")); assert isinstance(steps, list)
    except Exception as e:
        print(f"cannot read plan: {e}"); return 2
    probs, by = [], {}
    for s in steps:
        sid = s.get("id", "?")
        miss = [k for k in REQ if k not in s or s[k] in (None, "")]
        if "depends_on" in miss and s.get("depends_on") == []:
            miss.remove("depends_on")
        if "behavior_change" in miss and s.get("behavior_change") is False:
            miss.remove("behavior_change")
        if miss:
            probs.append(f"{sid}: missing {miss}")
        if sid in by:
            probs.append(f"{sid}: duplicate id")
        by[sid] = s
        if s.get("type") not in TYPES:
            probs.append(f"{sid}: type must be one of {sorted(TYPES)}")
        try:
            if float(s.get("hours", 0)) > 16:
                probs.append(f"{sid}: {s['hours']}h > 16h: split the step")
        except (TypeError, ValueError):
            probs.append(f"{sid}: hours must be a number")
        if s.get("behavior_change") is True:
            probs.append(f"{sid}: behavior_change=true: separate behaviour changes from refactoring steps")
    for sid, s in by.items():
        for d in s.get("depends_on", []):
            if d not in by:
                probs.append(f"{sid}: depends_on unknown step {d}")
    state, order = {}, []

    def visit(n, path):
        if state.get(n) == 2:
            return
        if state.get(n) == 1:
            probs.append("cycle: " + " -> ".join(path + [n])); return
        state[n] = 1
        for d in sorted(by[n].get("depends_on", []), key=lambda x: float(by.get(x, {}).get("hours", 0) or 0)):
            if d in by:
                visit(d, path + [n])
        state[n] = 2; order.append(n)

    for n in sorted(by, key=lambda x: float(by[x].get("hours", 0) or 0)):
        visit(n, [])

    def ancestors(n, seen=None):
        seen = seen if seen is not None else set()
        for d in by[n].get("depends_on", []):
            if d in by and d not in seen:
                seen.add(d); ancestors(d, seen)
        return seen
    if not any(p.startswith("cycle") for p in probs):
        for sid, s in by.items():
            anc = ancestors(sid)
            types = {by[a].get("type") for a in anc}
            if s.get("type") in NEED_TESTS and not s.get("tests_exist") and "CHARACTERIZE" not in types:
                probs.append(f"{sid}: {s['type']} without a CHARACTERIZE step in its dependencies (or tests_exist=true)")
            if s.get("type") in ("REPLACE", "DELETE") and not types & {"SEAM", "MOVE", "CHARACTERIZE"} and not s.get("tests_exist"):
                probs.append(f"{sid}: {s['type']} is first in its chain: add a SEAM/CHARACTERIZE before it")
    for p in probs:
        print("PROBLEM", p)
    if not any(p.startswith("cycle") for p in probs):
        total = sum(float(by[n].get("hours", 0) or 0) for n in order)
        longest = {}
        for n in order:
            longest[n] = float(by[n].get("hours", 0) or 0) + max([longest[d] for d in by[n].get("depends_on", []) if d in longest] or [0])
        end = max(longest, key=longest.get) if longest else None
        print("ORDER:", " -> ".join(order))
        print(f"total {total:g}h | critical path {longest.get(end, 0):g}h ending at {end}")
    print(f"{len(steps)} steps, {len(probs)} problems")
    return 1 if probs else 0


if __name__ == "__main__":
    sys.exit(main())
