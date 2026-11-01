#!/usr/bin/env python3
"""Check an assumption ledger: schema, expiry, missing tripwires, and (optionally) live checks.

Usage: python scripts/tripwire_check.py <ledger.json> [--run] [--warn-days N] [--today YYYY-MM-DD]

Ledger entry fields
  always:    id, assumption, evidence, confidence (VERIFIED|BELIEVED|GUESSED),
             impact (HIGH|MEDIUM|LOW), expires (YYYY-MM-DD), owner
  tripwire:  check (human description), check_command (argv-style command string),
             threshold, on_trigger

A tripwire is REQUIRED when  impact=HIGH and confidence != VERIFIED,
                         or  impact=MEDIUM and confidence=GUESSED.
Findings: INVALID (schema), EXPIRED, EXPIRING (<= warn-days), UNMONITORED (tripwire required but
no check_command), TRIPPED (check_command exit code != 0), CHECK-ERROR (cannot run / timeout 60s).
--run executes check_command WITHOUT a shell (shlex split). Contract: exit 0 = assumption still
holds, non-zero = tripped. Only run ledgers you trust: they contain commands.
Exit code: 0 clean, 1 findings, 2 usage/input error. Standard library only.
"""
import datetime, json, shlex, subprocess, sys

ALWAYS = ["id", "assumption", "evidence", "confidence", "impact", "expires", "owner"]
TRIPWIRE = ["check", "threshold", "on_trigger"]
CONF = {"VERIFIED", "BELIEVED", "GUESSED"}
IMPACT = {"HIGH", "MEDIUM", "LOW"}


def tripwire_required(it):
    c, i = it.get("confidence"), it.get("impact")
    return (i == "HIGH" and c != "VERIFIED") or (i == "MEDIUM" and c == "GUESSED")


def main():
    argv = sys.argv[1:]
    def opt(name, default):
        if name in argv:
            i = argv.index(name); v = argv[i + 1]; del argv[i:i + 2]; return v
        return default
    warn_days = int(opt("--warn-days", 30))
    today = datetime.date.fromisoformat(opt("--today", datetime.date.today().isoformat()))
    run = "--run" in argv
    pos = [a for a in argv if not a.startswith("--")]
    if not pos:
        print(__doc__); return 2
    try:
        items = json.load(open(pos[0], encoding="utf-8"))
        assert isinstance(items, list)
    except Exception as e:
        print(f"cannot read ledger: {e}"); return 2
    findings, seen = 0, set()

    def report(tag, kind, msg):
        nonlocal findings
        print(f"[{kind}] {tag}: {msg}"); findings += 1

    for it in items:
        tag = it.get("id", "?")
        if tag in seen:
            report(tag, "INVALID", "duplicate id")
        seen.add(tag)
        missing = [k for k in ALWAYS if not it.get(k)]
        if it.get("confidence") not in CONF: missing.append("confidence(valid)")
        if it.get("impact") not in IMPACT: missing.append("impact(valid)")
        need = tripwire_required(it)
        if need:
            missing += [k for k in TRIPWIRE if not it.get(k)]
        if missing:
            report(tag, "INVALID", f"missing/invalid fields {sorted(set(missing))}")
        try:
            days = (datetime.date.fromisoformat(it["expires"]) - today).days
            if days < 0:
                report(tag, "EXPIRED", f"{-days} days ago; re-verify: {it['assumption']}")
            elif days <= warn_days:
                report(tag, "EXPIRING", f"in {days} days: {it['assumption']}")
        except (KeyError, ValueError):
            report(tag, "INVALID", "expires must be YYYY-MM-DD")
        cmd = it.get("check_command")
        if need and not cmd:
            report(tag, "UNMONITORED", "tripwire required but no check_command (a manual review date alone is not monitoring)")
        if run and cmd:
            try:
                r = subprocess.run(shlex.split(cmd), capture_output=True, text=True, timeout=60)
                if r.returncode != 0:
                    report(tag, "TRIPPED", f"{it.get('on_trigger', '(no on_trigger)')}\n{(r.stdout + r.stderr)[-300:]}")
            except Exception as e:
                report(tag, "CHECK-ERROR", f"{type(e).__name__}: {e}")
    print(f"\n{len(items)} assumptions, {findings} findings")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
