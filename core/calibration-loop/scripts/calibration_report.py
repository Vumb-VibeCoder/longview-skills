#!/usr/bin/env python3
"""Calibration report for a JSONL prediction log.

Usage: python scripts/calibration_report.py <log.jsonl> [--today YYYY-MM-DD]

Each line: {"id","date","prediction","confidence","resolution","check_on","outcome","notes"}
  confidence = probability (0.5-1.0) that the prediction is TRUE as worded.
  outcome    = null (unresolved) | true | false.
Reports: resolved/unresolved/overdue counts, Brier score (lower is better; always saying 0.5
scores 0.25), mean confidence vs hit rate (overconfidence = confidence - hit rate), and a
per-bucket table. Conclusions are withheld below 20 resolved predictions, and per bucket below
5. Standard library only.
"""
import datetime, json, sys


def main():
    argv = sys.argv[1:]
    today = datetime.date.today()
    if "--today" in argv:
        i = argv.index("--today"); today = datetime.date.fromisoformat(argv[i + 1]); del argv[i:i + 2]
    if not argv:
        print(__doc__); return 2
    rows, bad = [], 0
    for n, line in enumerate(open(argv[0], encoding="utf-8"), 1):
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
            assert 0.5 <= float(r["confidence"]) <= 1.0 and r["prediction"] and r["check_on"] and r["resolution"]
            assert r.get("outcome") in (None, True, False)
            datetime.date.fromisoformat(r["check_on"])
            rows.append(r)
        except Exception:
            bad += 1; print(f"line {n}: invalid (need prediction, resolution, check_on, 0.5<=confidence<=1, outcome null/true/false)")
    done = [r for r in rows if r.get("outcome") is not None]
    open_ = [r for r in rows if r.get("outcome") is None]
    overdue = [r for r in open_ if datetime.date.fromisoformat(r["check_on"]) < today]
    print(f"entries: {len(rows)} | resolved: {len(done)} | unresolved: {len(open_)} | overdue: {len(overdue)} | invalid lines: {bad}")
    for r in overdue:
        print(f"  OVERDUE {r['id']} (due {r['check_on']}): resolve it -> {r['resolution']}")
    if not done:
        print("nothing resolved yet: no calibration can be computed"); return 1 if bad or overdue else 0
    brier = sum((float(r["confidence"]) - (1.0 if r["outcome"] else 0.0)) ** 2 for r in done) / len(done)
    hit = sum(1 for r in done if r["outcome"]) / len(done)
    conf = sum(float(r["confidence"]) for r in done) / len(done)
    print(f"Brier: {brier:.3f} (0.25 = coin-flip baseline) | mean confidence {conf:.2f} | hit rate {hit:.2f} | overconfidence {conf - hit:+.2f}")
    print("bucket      n   mean_conf  hit_rate  reading")
    for lo in (0.5, 0.6, 0.7, 0.8, 0.9):
        b = [r for r in done if lo <= float(r["confidence"]) < lo + 0.1 or (lo == 0.9 and float(r["confidence"]) == 1.0)]
        if not b:
            continue
        c = sum(float(r["confidence"]) for r in b) / len(b); h = sum(1 for r in b if r["outcome"]) / len(b)
        reading = "n too small (<5)" if len(b) < 5 else ("overconfident" if c - h > 0.1 else "underconfident" if h - c > 0.1 else "ok")
        print(f"{lo:.1f}-{lo + 0.1:.1f}  {len(b):>3}   {c:.2f}       {h:.2f}      {reading}")
    if len(done) < 20:
        print(f"SAMPLE TOO SMALL: {len(done)} resolved (<20). Treat the numbers above as anecdotes, not calibration.")
    return 1 if bad or overdue else 0


if __name__ == "__main__":
    sys.exit(main())
