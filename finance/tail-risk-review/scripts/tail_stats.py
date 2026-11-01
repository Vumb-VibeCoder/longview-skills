#!/usr/bin/env python3
"""Tail statistics for a series of periodic returns (decimals, e.g. -0.04). Standard library only.
Usage: python tail_stats.py returns.json|returns.txt [--alpha 0.05]
Input: JSON array or one number per line."""
import json, sys, math

def load(p):
    t = open(p).read().strip()
    try:
        d = json.loads(t)
        if isinstance(d, list): return [float(x) for x in d]
    except ValueError:
        pass
    return [float(x) for x in t.replace(",", "\n").split()]

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    r = load(sys.argv[1])
    a = float(sys.argv[sys.argv.index("--alpha") + 1]) if "--alpha" in sys.argv else 0.05
    n = len(r)
    if n < 10:
        print("ERROR need at least 10 observations"); sys.exit(2)
    mu = sum(r) / n
    sd = math.sqrt(sum((x - mu) ** 2 for x in r) / (n - 1))
    kurt = sum((x - mu) ** 4 for x in r) / n / (sd ** 4 if sd else 1) - 3
    s = sorted(r)
    k = max(1, int(math.floor(a * n)))
    var = -s[k - 1]                      # empirical loss at the alpha quantile
    cvar = -sum(s[:k]) / k               # mean loss in the worst alpha tail
    z = {0.01: 2.326, 0.025: 1.960, 0.05: 1.645, 0.10: 1.282}.get(a)
    nvar = (-(mu - z * sd)) if z else None
    ncvar = None
    if z:
        phi = math.exp(-z * z / 2) / math.sqrt(2 * math.pi)
        ncvar = -mu + sd * phi / a
    eq, peak, mdd = 1.0, 1.0, 0.0
    for x in r:
        eq *= (1 + x); peak = max(peak, eq); mdd = max(mdd, 1 - eq / peak)
    worst = s[:3]
    print(f"n={n} mean={mu:.4%} sd={sd:.4%} excess_kurtosis={kurt:.2f}")
    print(f"worst 3 periods: " + ", ".join(f"{x:.2%}" for x in worst) + f"  ({(mu - s[0]) / sd if sd else 0:.1f} sd below mean)")
    print(f"empirical VaR{int((1 - a) * 100)} loss={var:.2%}   CVaR (expected shortfall)={cvar:.2%}")
    if nvar is not None:
        print(f"normal-model VaR loss={nvar:.2%}   empirical/normal = {var / nvar:.2f}" if nvar > 0 else "normal-model VaR is not a loss")
    if ncvar and ncvar > 0:
        print(f"normal-model expected shortfall={ncvar:.2%}   empirical/normal = {cvar / ncvar:.2f}  (>1 means the real tail is worse than the bell curve says)")
    print(f"max drawdown (compounded)={mdd:.2%}")
    flags = []
    if ncvar and ncvar > 0 and cvar / ncvar > 1.3: flags.append("tail loss (CVaR) exceeds the normal-model estimate by >30%: judge risk by CVaR and worst cases, not by VaR")
    if n < 60: flags.append(f"SHORT SAMPLE (n={n}): the worst observed loss is only a LOWER bound on what can happen")
    if kurt > 1: flags.append("FAT TAILS (excess kurtosis > 1): a normal-distribution model understates extremes")
    if sd and (mu - s[0]) / sd > 4: flags.append("an observed move beyond 4 sd: treat normal-model risk numbers as invalid")
    if any(x <= -1 for x in r): flags.append("a period lost 100% or more: total ruin occurred in-sample")
    print("FLAGS: " + ("; ".join(flags) if flags else "none"))

if __name__ == "__main__":
    main()
