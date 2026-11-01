#!/usr/bin/env python3
"""One-at-a-time sensitivity and break-even finder. Standard library only.
Model JSON: {"formula": "units*price-cost", "threshold": 0,
  "inputs": {"units": {"base":1000,"low":600,"high":1200}, ...}}
Usage: python sensitivity.py model.json"""
import ast, json, sys, math

ALLOWED = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Load,
           ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.Call, ast.Mod)
FUNCS = {"min": min, "max": max, "abs": abs, "sqrt": math.sqrt, "log": math.log, "exp": math.exp}

def compile_formula(src, names):
    tree = ast.parse(src, mode="eval")
    for node in ast.walk(tree):
        if not isinstance(node, ALLOWED):
            raise ValueError(f"disallowed syntax: {type(node).__name__}")
        if isinstance(node, ast.Name) and node.id not in names and node.id not in FUNCS:
            raise ValueError(f"unknown name in formula: {node.id}")
        if isinstance(node, ast.Call) and not (isinstance(node.func, ast.Name) and node.func.id in FUNCS):
            raise ValueError("only min/max/abs/sqrt/log/exp calls are allowed")
    return lambda env: _ev(tree.body, env)

MAX_POW = 1000.0  # refuse absurd exponents/bases instead of hanging on e.g. 9**9**9**9

def _ev(n, env):
    """Tiny evaluator for the whitelisted syntax only (no eval)."""
    if isinstance(n, ast.Constant):
        if isinstance(n.value, bool) or not isinstance(n.value, (int, float)):
            raise ValueError("only numeric constants are allowed")
        return n.value
    if isinstance(n, ast.Name):
        return FUNCS[n.id] if n.id in FUNCS else env[n.id]
    if isinstance(n, ast.UnaryOp):
        v = _ev(n.operand, env)
        return -v if isinstance(n.op, ast.USub) else +v
    if isinstance(n, ast.BinOp):
        a, b = _ev(n.left, env), _ev(n.right, env)
        op = n.op
        if isinstance(op, ast.Add): return a + b
        if isinstance(op, ast.Sub): return a - b
        if isinstance(op, ast.Mult): return a * b
        if isinstance(op, ast.Div): return a / b
        if isinstance(op, ast.Mod): return a % b
        if isinstance(op, ast.Pow):
            if abs(b) > MAX_POW or abs(a) > 1e12:
                raise ValueError("exponent or base too large")
            return float(a) ** b
    if isinstance(n, ast.Call):
        return _ev(n.func, env)(*[_ev(x, env) for x in n.args])
    raise ValueError(f"disallowed syntax: {type(n).__name__}")

def breakeven(f, env, name, thr, lo, hi):
    a, b = lo, hi
    fa, fb = f({**env, name: a}) - thr, f({**env, name: b}) - thr
    if fa == 0: return a
    if fb == 0: return b
    if fa * fb > 0: return None
    for _ in range(200):
        mid = (a + b) / 2
        fm = f({**env, name: mid}) - thr
        if fa * fm <= 0: b, fb = mid, fm
        else: a, fa = mid, fm
    return (a + b) / 2

def die(msg):
    print("ERROR: " + msg, file=sys.stderr); sys.exit(2)

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(2)
    try:
        with open(sys.argv[1], encoding="utf-8") as fh:
            m = json.load(fh)
        inputs, thr = m["inputs"], m.get("threshold", 0.0)
        for k, v in inputs.items():
            if not (v["low"] <= v["base"] <= v["high"]):
                die(f"{k}: need low <= base <= high")
        f = compile_formula(m["formula"], set(inputs))
        run_model(f, inputs, thr)
    except (OSError, ValueError, KeyError, TypeError, SyntaxError, ZeroDivisionError, OverflowError) as e:
        die(f"{type(e).__name__}: {e}")

def run_model(f, inputs, thr):
    base_env = {k: v["base"] for k, v in inputs.items()}
    base = f(base_env)
    print(f"base output = {base:.4g}   threshold = {thr}   base side = {'above' if base >= thr else 'below'}")
    rows = []
    for k, v in inputs.items():
        lo_out = f({**base_env, k: v["low"]}); hi_out = f({**base_env, k: v["high"]})
        span = abs(v["base"]) * 5 if v["base"] else (v["high"] - v["low"]) * 5 or 1
        be = breakeven(f, base_env, k, thr, v["base"] - span, v["base"] + span)
        flips = (lo_out >= thr) != (base >= thr) or (hi_out >= thr) != (base >= thr)
        rows.append((abs(hi_out - lo_out), k, lo_out, hi_out, be, flips, v))
    rows.sort(reverse=True)
    print(f"{'input':14}{'out@low':>12}{'out@high':>12}{'swing':>12}{'break-even':>14}  flip-in-range")
    for sw, k, lo_o, hi_o, be, flips, v in rows:
        bes = "none in 5x" if be is None else f"{be:.4g}"
        print(f"{k:14}{lo_o:12.4g}{hi_o:12.4g}{sw:12.4g}{bes:>14}  {'YES' if flips else 'no'}")
    fl = [k for _, k, _, _, _, fl, _ in rows if fl]
    print("DECISION FLIPS inside the stated range for: " + (", ".join(fl) if fl else "nothing (robust to single-input moves)"))
    print("Note: one-at-a-time; combined moves of several inputs can flip it even when this says robust.")

if __name__ == "__main__":
    main()
