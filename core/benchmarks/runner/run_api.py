#!/usr/bin/env python3
"""(Optional) Send prompts to the Claude API and collect responses.json. Not tested against the real API:
run 1-2 cases first. Needs the ANTHROPIC_API_KEY environment variable.
A failed call or unparseable answer is recorded as {"error": ...}; score.py counts it as MISSING,
never as "not flagged".

Usage: python run_api.py --prompts out/baseline --out out/baseline/responses.json [--model claude-sonnet-5-5]
"""
import argparse, glob, json, os, re, urllib.request, urllib.error


def call(model, prompt, key):
    body = json.dumps({"model": model, "max_tokens": 400, "messages": [{"role": "user", "content": prompt}]}).encode()
    req = urllib.request.Request("https://api.anthropic.com/v1/messages", data=body, headers={
        "content-type": "application/json", "x-api-key": key, "anthropic-version": "2023-06-01"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = json.load(r)
    return "".join(b.get("text", "") for b in data.get("content", []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="claude-sonnet-5-5")
    a = ap.parse_args()
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise SystemExit("ANTHROPIC_API_KEY is not set")
    res = {}
    for f in sorted(glob.glob(os.path.join(a.prompts, "*.md"))):
        cid = os.path.splitext(os.path.basename(f))[0]
        try:
            text = call(a.model, open(f, encoding="utf-8").read(), key)
            m = re.search(r"\{.*\}", text, re.S)
            res[cid] = json.loads(m.group(0)) if m else {"error": "could not parse a JSON object from the answer"}
        except (urllib.error.URLError, json.JSONDecodeError) as e:
            res[cid] = {"error": str(e)}
        print(cid, res[cid].get("flag", "ERROR"))
    json.dump(res, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
