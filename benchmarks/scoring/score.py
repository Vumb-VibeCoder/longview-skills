#!/usr/bin/env python3
"""Score the AI: how many real problems it caught and how many false alarms it raised, with vs without skills.

Usage:
  python score.py --cases ../cases [--verified-only] --results baseline=out/baseline/responses.json --results skill=out/with_skill/responses.json
responses.json: {"<case id>": {"flag": true, "pattern": "M03", "reason": "..."}, ...}
An entry without a boolean "flag" (for example {"error": ...}) or an absent case counts as MISSING, not as "not flagged".
"""
import argparse, glob, json, os


def load_cases(d, verified_only=False):
    """Cases whose label a person marked invalid are always dropped; --verified-only keeps only label_check == valid."""
    out, dropped = {}, 0
    for f in glob.glob(os.path.join(d, "*.json")):
        c = json.load(open(f, encoding="utf-8"))
        chk = c.get("label_check")
        if chk == "invalid" or (verified_only and chk != "valid"):
            dropped += 1
            continue
        out[c["id"]] = c
    return out, dropped


def score(cases, res):
    tp = fp = fn = tn = miss = 0
    for cid, c in cases.items():
        r = res.get(cid)
        if not isinstance(r, dict) or not isinstance(r.get("flag"), bool):
            miss += 1
            continue
        flag, pos = r["flag"], c["label"] == "positive"
        if pos and flag: tp += 1
        elif pos: fn += 1
        elif flag: fp += 1
        else: tn += 1
    prec = tp / (tp + fp) if tp + fp else 0.0
    rec = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * prec * rec / (prec + rec) if prec + rec else 0.0
    far = fp / (fp + tn) if fp + tn else 0.0
    return dict(tp=tp, fp=fp, fn=fn, tn=tn, precision=prec, recall=rec, f1=f1, false_alarm_rate=far, missing=miss)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="../cases")
    ap.add_argument("--results", action="append", required=True, help="name=path.json")
    ap.add_argument("--verified-only", action="store_true", help="score only cases a person marked label_check=valid")
    a = ap.parse_args()
    cases, dropped = load_cases(a.cases, a.verified_only)
    if dropped:
        print(f"({dropped} case(s) excluded by label review)")
    if not cases:
        raise SystemExit("no cases found in " + a.cases)
    npos = sum(c["label"] == "positive" for c in cases.values())
    print(f"{len(cases)} cases ({npos} positive, {len(cases) - npos} control)")
    if len(cases) < 30:
        print("WARNING: fewer than 30 cases. Treat the numbers as an indication only; one decision moves recall by up to "
              f"{1 / max(npos, 1):.0%}.")
    print(f"\n{'condition':<14}{'precision':>10}{'recall':>9}{'F1':>7}{'false alarm':>13}   TP FP FN TN")
    results = {}
    for spec in a.results:
        name, _, path = spec.partition("=")
        s = results[name] = score(cases, json.load(open(path, encoding="utf-8")))
        print(f"{name:<14}{s['precision']:>10.2f}{s['recall']:>9.2f}{s['f1']:>7.2f}{s['false_alarm_rate']:>13.2f}   "
              f"{s['tp']:>2} {s['fp']:>2} {s['fn']:>2} {s['tn']:>2}" + (f"  (missing {s['missing']})" if s['missing'] else ""))
    if any(s["missing"] for s in results.values()):
        print("\nWARNING: some conditions have missing answers; their numbers are not comparable with complete runs.")
    names = list(results)
    if len(names) >= 2:
        b, k = results[names[0]], results[names[1]]
        keep = k["f1"] > b["f1"] and k["false_alarm_rate"] <= b["false_alarm_rate"] + 0.05
        print(f"\nRule: keep a skill only if F1 rises AND the false alarm rate does not rise noticeably (here: more than 0.05).")
        print(f"{names[1]} vs {names[0]}: F1 {k['f1'] - b['f1']:+.2f}, false alarm {k['false_alarm_rate'] - b['false_alarm_rate']:+.2f} -> "
              + ("KEEP candidate" if keep else "NOT shown to help"))


if __name__ == "__main__":
    main()
