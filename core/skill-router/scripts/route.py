#!/usr/bin/env python3
"""Keyword router for Longview skills. Standard library only.
Usage:
  python route.py "request text"          print a suggested skill set (heuristic)
  python route.py --test [cases.json]     run the regression set; exit 1 if any case fails
Output of the first form: class hint, artifact warning, and at most 4 suggested skills.
The SKILL.md routing table wins over this script when they disagree."""
import json, os, re, sys

# skill -> (weight, regex). Higher weight wins when more than 4 match.
RULES = {
 "long-horizon-cashflow": (5, r"will (the|my) (money|savings)|last \d+ years|runway|retire|withdraw|cash ?flow|monthly (budget|income|expenses)|savings"),
 "scenario-stress-test": (3, r"stress|worst case|downside|income (drop|loss)|revenue (drop|fall)s?|drops? \d+%|shock|adverse|loan|what if (i|we|income|prices?) "),
 "assumption-sensitivity": (4, r"\broi\b|break.?even|pricing|business case|buy vs|rent vs|which (input|assumption)|sensitiv|biggest driver"),
 "tail-risk-review": (5, r"portfolio|drawdown|\bruin\b|tail risk|leverage|position siz|crash|extreme loss"),
 "decision-regret-check": (5, r"regret|buy or wait|commit or keep|hard choice|under uncertainty|option a or b|which option"),
 "design-token-discipline": (5, r"design token|hard-?coded colou?r|dark mode|css variable|spacing scale|rebrand|theming|\btheme\b"),
 "consistency-audit": (4, r"inconsisten|patched together|look(s)? different|before a redesign|design system onboarding"),
 "component-api-stability": (5, r"\bprops\b|component api|ui library|shared component|deprecat\w* .*component|release .*component"),
 "accessibility-and-platform-drift": (5, r"accessib|a11y|wcag|screen reader|keyboard nav|colou?r contrast"),
 "dependency-risk": (5, r"dependenc|package\.json|requirements\.txt|pyproject|\bnpm\b|\bpip\b|vendor lock|third.party librar|which librar"),
 "module-boundary-review": (5, r"\bmodules?\b|boundar|circular import|import cycle|coupling|split .*service|where should .* live"),
 "codebase-longevity-audit": (5, r"audit (the|this|our) (codebase|repo)|take ?over|inherit(ed)?|rewrite or|repo health|keep patching|should we rewrite"),
 "logic-myopia-audit": (4, r"fixes keep|keeps breaking|special.?case|bug.?fix cycle|fragile|invariant"),
 "line-durability": (5, r"review (this|the) (code|function|file|snippet)|except:|hard-?coded|magic number|def \w+\(|function that|write a (script|function)"),
 "debt-ledger": (4, r"tech(nical)? debt|shortcut|quick fix|hack for now"),
 "refactor-planner": (4, r"refactor|restructure|clean ?up the"),
 "fitness-functions": (5, r"ci check|guardrail|architecture test|enforce .*rule|lint rule|fail the build"),
 "adr-writer": (4, r"\badr\b|decision record|document (the|this) decision|why did we"),
 "archaeology-test": (5, r"handover|hand over|new hire|can a stranger|maintainable by someone"),
 "change-injection": (4, r"how (hard|easy) is it to (add|change)|measure (the )?flexib|blast radius"),
 "extensibility-review": (5, r"plugin|extension point|abstraction layer|add .* easily|configurable|over-?built|too rigid"),
 "council-protocol": (3, r"should (we|i) (add|build|use|adopt)|do more or less|over-?engineer|trade-?off|torn between"),
 "reversibility-check": (4, r"one-way|hard to undo|\bschema\b|migrat|public api|which database|choose (a |the )?(database|stack)|vendor"),
 "rollback-path": (5, r"roll ?back|undo (this|the|a) (change|deploy|migration)|drop\b.{0,30}\b(table|column)s?\b|\bmigrat(e|es|ing|ion)\b.{0,40}(production|prod\b|live|database|schema|data)|delete (all|the|old) (data|rows|records|files)|backfill|deploy(ing|ment)? to prod|go live|cut ?over|database migration"),
 "security-durability": (5, r"secur|requests\.(get|post|put|delete)\(|urlopen\(|\bfetch\(|\baxios\b|http://|vulnerab|\bauth(entication|orization)?\b|password|credential|\bsecrets?\b|api key|\btoken\b|encrypt|injection|\bxss\b|csrf|pentest|personal data|\bpii\b|gdpr|make (the|this) repo public|open.?source it"),
 "test-durability": (5, r"\btests?\b|test suite|unit test|flaky|test coverage|\bpytest\b|\bjest\b|tests? (pass|fail)|regression test|characteri[sz]ation"),
 "three-horizon-map": (2, r"in (3|5|10) years|years from now|will it scale|future-?proof"),
 "system-design-longevity": (5, r"design (a|the|this)|architecture|data model|api design|pipeline|\bservice\b|\bsync\b|integration"),
 "failure-and-scale-modes": (4, r"outage|retr(y|ies)|queue|\bscale\b|high load|partner|\bsync\b|integration|goes down"),
 "assumption-ledger": (3, r"\bassum(e|ption|ptions|ing)\b|what are we assuming"),
 "assumption-tripwires": (4, r"tripwire|how would we know|monitor .*assum|assumption .*expir"),
 "calibration-loop": (5, r"brier|calibrat|how reliable were|check (this|my) prediction later"),
 "change-vectors": (3, r"what (is likely|will) (to )?change|requirements change|likely to change"),
}
MONEY = r"money|payment|invoice|billing|price|tax|order total|customer data|personal data|\bpii\b|password|credential|\bauth\b|live (shop|site|service|app)|production|real users|users depend|for years"
ONEOFF = r"\bonce\b|one[- ]off|one[- ]time|throwaway|throw-?away|quick script|prototype"
ARTIFACT = r"```|def |class |function |\bimport |https?://|\d{3,}|\bselect\b|\.py|\.js|\.ts|\.css|diagram|attached|here is|below|\brepo\b|codebase|this project"
REVIEW = r"\breview\b|\baudit\b|\bassess\b|\bevaluate\b|long-term risk"

def route(text):
    t = text.lower()
    hits = [(w, s) for s, (w, rx) in RULES.items() if re.search(rx, t)]
    hits.sort(key=lambda x: -x[0])
    skills = [s for _, s in hits][:4]
    cls = "C+ (escalator: money/data/users/years)" if re.search(MONEY, t) else ("A/B (one-off or prototype)" if re.search(ONEOFF, t) else "unknown: ask or mark PROVISIONAL")
    if cls.startswith("C+") and re.search(ONEOFF, t): cls = "C+ (escalator beats one-off wording)"
    needs_artifact = bool(re.search(REVIEW, t)) and not re.search(ARTIFACT, text)
    if cls.startswith("A/B"): skills = []
    return {"class_hint": cls, "insufficient_evidence": needs_artifact, "skills": skills}

def run_tests(path):
    cases = json.load(open(path, encoding="utf-8"))
    bad = 0
    for c in cases:
        r = route(c["request"])
        got = set(r["skills"])
        missing = set(c.get("must_include", [])) - got
        extra = set(c.get("must_exclude", [])) & got
        cls_ok = c.get("class") is None or r["class_hint"].startswith(c["class"])
        ie_ok = c.get("insufficient_evidence", False) == r["insufficient_evidence"]
        if missing or extra or not cls_ok or not ie_ok:
            bad += 1
            print(f"FAIL {c['id']}: missing={sorted(missing)} unwanted={sorted(extra)} class_ok={cls_ok} ie_ok={ie_ok} got={sorted(got)} class={r['class_hint']}")
    print(f"{len(cases)-bad}/{len(cases)} routing cases passed")
    return 1 if bad else 0

if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    if len(sys.argv) >= 2 and sys.argv[1] == "--test":
        sys.exit(run_tests(sys.argv[2] if len(sys.argv) > 2 else os.path.join(here, "..", "templates", "route_cases.json")))
    if len(sys.argv) < 2: sys.exit("usage: route.py \"request\" | --test [cases.json]")
    r = route(" ".join(sys.argv[1:]))
    print("horizon-fit (always first)")
    print("class hint:", r["class_hint"])
    if r["insufficient_evidence"]: print("WARNING: review requested but no artifact seen -> VERDICT: INSUFFICIENT EVIDENCE, list needed inputs")
    print("suggested:", ", ".join(r["skills"]) or "none beyond horizon-fit")
