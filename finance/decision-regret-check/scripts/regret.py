#!/usr/bin/env python3
"""Regret matrix for a decision. Standard library only.
JSON: {"options":["A","B"], "scenarios":["good","bad"], "payoff":[[10,-5],[4,3]],
       "probs":[0.7,0.3]}   (payoff[i][j] = outcome of option i in scenario j, higher is better; probs optional)
Usage: python regret.py decision.json"""
import json, sys

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    d = json.load(open(sys.argv[1], encoding="utf-8"))
    O, S, P = d["options"], d["scenarios"], d["payoff"]
    if len(P) != len(O) or any(len(r) != len(S) for r in P):
        print("ERROR payoff must be options x scenarios"); sys.exit(2)
    probs = d.get("probs")
    if probs is not None and (len(probs) != len(S) or abs(sum(probs) - 1) > 1e-6):
        print("ERROR probs must match scenarios and sum to 1"); sys.exit(2)
    best = [max(P[i][j] for i in range(len(O))) for j in range(len(S))]
    R = [[best[j] - P[i][j] for j in range(len(S))] for i in range(len(O))]
    maxreg = [max(r) for r in R]
    worst = [min(r) for r in P]
    print(f"{'option':12}{'worst case':>12}{'max regret':>12}" + ("{:>14}".format("expected") if probs else ""))
    ev = [sum(p * x for p, x in zip(probs, P[i])) for i in range(len(O))] if probs else None
    for i, o in enumerate(O):
        print(f"{o:12}{worst[i]:12.4g}{maxreg[i]:12.4g}" + (f"{ev[i]:14.4g}" if ev else ""))
    mm = min(range(len(O)), key=lambda i: maxreg[i])
    mx = max(range(len(O)), key=lambda i: worst[i])
    print(f"minimax-regret choice: {O[mm]}   |   maximin (best worst case): {O[mx]}")
    if ev:
        eb = max(range(len(O)), key=lambda i: ev[i])
        print(f"expected-value choice: {O[eb]}")
        if eb != mm:
            print("CONFLICT: expected value and minimax regret disagree: decide which loss you cannot live with, then pick.")
    dom = [O[i] for i in range(len(O)) if any(k != i and all(P[k][j] >= P[i][j] for j in range(len(S))) and any(P[k][j] > P[i][j] for j in range(len(S))) for k in range(len(O)))]
    print("dominated options (never better in any scenario): " + (", ".join(dom) if dom else "none"))

if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError, IndexError) as _e:  # bad input -> exit 2, not a traceback
        print(f"ERROR: {type(_e).__name__}: {_e}", file=sys.stderr); sys.exit(2)
