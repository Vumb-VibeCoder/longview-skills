#!/usr/bin/env python3
"""Pay-or-accept calculator for technical debt (works for any debt with a principal and an interest).

Single debt:
  python scripts/debt_calc.py --principal 8 --interest 1.5 [--residual 0] [--horizon 12] [--margin 1.5]
Ledger file:
  python scripts/debt_calc.py --ledger debt.json [--horizon 12] [--margin 1.5] [--today YYYY-MM-DD]

principal  hours to fix NOW (include tests, migration, review)
interest   extra hours PER MONTH the debt costs if left alone (slower work, bugs, re-explaining)
residual   interest that remains AFTER the fix (default 0)
horizon    months the affected code is still expected to live (from horizon-fit); per-debt
           "horizon_months" in the ledger overrides --horizon
margin     safety factor on principal (default 1.5) because fix estimates are usually optimistic

net interest = interest - residual.  breakeven = principal / net interest (months).
Decision (needs a horizon):  saved = net x horizon
  PAY NOW   saved >= margin x principal
  MARGINAL  principal <= saved < margin x principal  -> accept, re-check at 'due'
  ACCEPT    saved < principal, or net interest <= 0 (fixing saves nothing)
Debt that nobody touches has interest 0: accepting it is correct. Interactions between debts
(one raising another's interest) are NOT modelled; adjust the estimates by hand.
Ledger fields: id, what, basis (how the numbers were estimated), principal_hours,
interest_hours_per_month, owner, due (YYYY-MM-DD), why_taken; optional residual_hours_per_month,
horizon_months. Exit code 1 if any entry is invalid or overdue. Standard library only.
"""
import argparse, datetime, json, sys

REQUIRED = ["id", "what", "basis", "principal_hours", "interest_hours_per_month", "owner", "due", "why_taken"]


def decide(principal, interest, residual, horizon, margin):
    net = interest - residual
    if principal <= 0:
        return "PAY NOW", None, net, "fix is free"
    if net <= 0:
        return "ACCEPT", None, net, "fixing saves nothing (net interest <= 0)"
    be = principal / net
    if horizon is None:
        return "NEEDS HORIZON", be, net, f"breakeven {be:.1f} months; compare with remaining lifetime"
    saved = net * horizon
    if saved >= margin * principal:
        return "PAY NOW", be, net, f"saves {saved:g}h over {horizon:g} months vs {principal:g}h (margin x{margin:g})"
    if saved >= principal:
        return "MARGINAL", be, net, f"saves {saved:g}h vs {principal:g}h but under margin x{margin:g}: accept, re-check at due"
    return "ACCEPT", be, net, f"saves only {saved:g}h over {horizon:g} months vs {principal:g}h"


def main():
    ap = argparse.ArgumentParser(description="debt calculator")
    ap.add_argument("--principal", type=float); ap.add_argument("--interest", type=float)
    ap.add_argument("--residual", type=float, default=0.0); ap.add_argument("--horizon", type=float)
    ap.add_argument("--margin", type=float, default=1.5); ap.add_argument("--ledger")
    ap.add_argument("--today", default=datetime.date.today().isoformat())
    a = ap.parse_args()
    if not a.ledger:
        if a.principal is None or a.interest is None:
            ap.error("give --principal and --interest, or --ledger")
        v, be, net, why = decide(a.principal, a.interest, a.residual, a.horizon, a.margin)
        print(f"{v}: {why}")
        if be is not None:
            print(f"principal {a.principal:g}h | net interest {net:g}h/month | breakeven {be:.1f} months | relative rate {net / a.principal:.1%}/month")
        return 0
    today = datetime.date.fromisoformat(a.today)
    try:
        items = json.load(open(a.ledger, encoding="utf-8")); assert isinstance(items, list)
    except Exception as e:
        print(f"cannot read ledger: {e}"); return 2
    problems, rows = 0, []
    for it in items:
        tag = it.get("id", "?")
        miss = [k for k in REQUIRED if it.get(k) in (None, "")]
        try:
            P, I = float(it["principal_hours"]), float(it["interest_hours_per_month"])
            R = float(it.get("residual_hours_per_month", 0))
            assert P >= 0 and I >= 0 and R >= 0
            due = datetime.date.fromisoformat(it["due"])
        except Exception:
            print(f"[INVALID] {tag}: missing/invalid fields {miss or ['numbers/due']}"); problems += 1; continue
        if miss:
            print(f"[INVALID] {tag}: missing fields {miss}"); problems += 1; continue
        h = it.get("horizon_months", a.horizon)
        v, be, net, why = decide(P, I, R, float(h) if h is not None else None, a.margin)
        if due < today:
            print(f"[OVERDUE] {tag}: due {it['due']} (re-evaluate or pay)"); problems += 1
        rows.append((net / P if P > 0 and net > 0 else 0, tag, it["what"], P, net, be, v, why))
    order = {"PAY NOW": 0, "MARGINAL": 1, "NEEDS HORIZON": 2, "ACCEPT": 3}
    rows.sort(key=lambda r: (order[r[6]], -r[0]))
    print(f"{'id':<6}{'decision':<14}{'principal':>10}{'net/mo':>8}{'breakeven':>11}  what")
    for rate, tag, what, P, net, be, v, why in rows:
        print(f"{tag:<6}{v:<14}{P:>9g}h{net:>7g}h{(f'{be:.1f}m' if be else '-'):>11}  {what}  [{why}]")
    tp = sum(r[3] for r in rows); ti = sum(r[4] for r in rows if r[4] > 0)
    print(f"\nTOTAL principal {tp:g}h | total net interest {ti:g}h/month | entries {len(rows)} | problems {problems}")
    pay = [r for r in rows if r[6] == "PAY NOW"]
    print(f"PAY NOW set: {sum(r[3] for r in pay):g}h principal removes {sum(r[4] for r in pay):g}h/month of interest")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
