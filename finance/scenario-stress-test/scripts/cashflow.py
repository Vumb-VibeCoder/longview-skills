#!/usr/bin/env python3
"""Monthly cashflow projection with scenarios. Standard library only.
Usage: python cashflow.py model.json [--json]
Exit code 1 if any scenario with must_survive != false runs out of cash."""
import json, sys, copy

def run(m):
    n = int(m["months"])
    infl = m.get("inflation_annual", 0.0)
    mi = (1 + infl) ** (1 / 12) - 1
    g_inc = (1 + m.get("income_growth_annual", 0.0)) ** (1 / 12) - 1
    g_exp = (1 + m.get("expense_growth_annual", infl)) ** (1 / 12) - 1
    shock_from = m.get("income_shock_from_month")
    shock = m.get("income_shock", 0.0)  # e.g. -0.4 = income falls 40% from that month
    one = {}
    for o in m.get("one_offs", []):
        one[int(o["month"])] = one.get(int(o["month"]), 0.0) + float(o["amount"])
    cash = float(m["start_cash"])
    low, low_m, first_neg = cash, 0, None
    for t in range(1, n + 1):
        inc = m["income_monthly"] * (1 + g_inc) ** t
        if shock_from is not None and t >= shock_from:
            inc *= (1 + shock)
        exp = m["expenses_monthly"] * (1 + g_exp) ** t
        cash += inc - exp + one.get(t, 0.0)
        if cash < low:
            low, low_m = cash, t
        if cash < 0 and first_neg is None:
            first_neg = t
    return {"final_nominal": round(cash, 2),
            "final_real": round(cash / (1 + mi) ** n, 2),
            "lowest_balance": round(low, 2), "lowest_month": low_m,
            "first_negative_month": first_neg}

def apply(base, sc):
    m = copy.deepcopy(base)
    for k, v in sc.items():
        if k in ("name", "must_survive", "add_one_offs"):
            continue
        m[k] = v
    m["one_offs"] = list(m.get("one_offs", [])) + list(sc.get("add_one_offs", []))
    return m

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    base = json.load(open(sys.argv[1]))
    for k in ("start_cash", "income_monthly", "expenses_monthly", "months"):
        if k not in base:
            print(f"ERROR missing field: {k}"); sys.exit(2)
    rows = [("BASE", True, run(base))]
    for sc in base.get("scenarios", []):
        rows.append((sc["name"], sc.get("must_survive", True), run(apply(base, sc))))
    if "--json" in sys.argv:
        print(json.dumps([{"scenario": n, **r} for n, _, r in rows], indent=2))
    else:
        print(f"{'scenario':28} {'final(nom)':>12} {'final(real)':>12} {'lowest':>12} {'@month':>6} {'cash<0 at':>9}")
        for n, _, r in rows:
            print(f"{n:28} {r['final_nominal']:12.0f} {r['final_real']:12.0f} {r['lowest_balance']:12.0f} {r['lowest_month']:6} {str(r['first_negative_month']):>9}")
    bad = [n for n, ms, r in rows if ms and r["first_negative_month"] is not None]
    if bad:
        print("FAIL: cash runs out in: " + ", ".join(bad)); sys.exit(1)
    print("OK: every must_survive scenario stays at or above zero")

if __name__ == "__main__":
    main()
