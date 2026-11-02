#!/usr/bin/env python3
"""Regression tests for the measurable scripts. Standard library only.
Run from the repo root:  python3 tests/test_regression.py
Each test runs a script as a subprocess and checks exit code and key output."""
import json, os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CF = os.path.join(ROOT, "finance", "long-horizon-cashflow")
CF2 = os.path.join(ROOT, "finance", "scenario-stress-test")
SENS = os.path.join(ROOT, "finance", "assumption-sensitivity")
REG = os.path.join(ROOT, "finance", "decision-regret-check")
DEBT = os.path.join(ROOT, "coding", "debt-ledger")

def run(script, *args):
    r = subprocess.run([sys.executable, "-I", script, *args], capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout, r.stderr

def tmp_json(obj, raw=None):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    f.write(raw if raw is not None else json.dumps(obj)); f.close()
    return f.name

BASE = {"start_cash": 1000, "income_monthly": 100, "expenses_monthly": 50, "months": 12}

class Cashflow(unittest.TestCase):
    script = os.path.join(CF, "scripts", "cashflow.py")

    def test_retirement_numbers_and_exit1(self):
        rc, out, _ = run(self.script, os.path.join(CF, "templates", "retirement.example.json"), "--json")
        rows = {x["scenario"]: x for x in json.JSONDecoder().raw_decode(out)[0]}
        self.assertEqual(rows["BASE"]["final_nominal"], 153225.57)
        self.assertEqual(rows["withdrawals indexed to 3%"]["first_negative_month"], 250)
        self.assertEqual(rc, 1)  # must_survive scenario fails on purpose

    def test_ok_exit0(self):
        rc, out, _ = run(self.script, tmp_json(BASE))
        self.assertEqual(rc, 0); self.assertIn("OK", out)

    def test_unknown_scenario_key_exit2(self):
        m = dict(BASE, scenarios=[{"name": "x", "must_survive": True, "income_shok": -1}])
        rc, _, err = run(self.script, tmp_json(m))
        self.assertEqual(rc, 2); self.assertIn("income_shok", err)

    def test_unknown_model_key_exit2(self):
        rc, _, err = run(self.script, tmp_json(dict(BASE, retrun_annual=0.05)))
        self.assertEqual(rc, 2); self.assertIn("retrun_annual", err)

    def test_missing_field_and_bad_file_exit2(self):
        self.assertEqual(run(self.script, tmp_json({"months": 3}))[0], 2)
        self.assertEqual(run(self.script, tmp_json(None, raw="{bad"))[0], 2)
        self.assertEqual(run(self.script, "/no/such/file.json")[0], 2)

    def test_return_needs_compounding_mode(self):
        self.assertEqual(run(self.script, tmp_json(dict(BASE, return_annual=0.05)))[0], 2)

    def test_scenario_shock_fails_must_survive(self):
        m = dict(BASE, months=60, expenses_monthly=90, scenarios=[{"name": "shock", "income_shock_from_month": 2, "income_shock": -0.5}])
        rc, out, _ = run(self.script, tmp_json(m))
        self.assertEqual(rc, 1); self.assertIn("shock", out)

    def test_two_copies_identical(self):
        a = open(self.script, "rb").read(); b = open(os.path.join(CF2, "scripts", "cashflow.py"), "rb").read()
        self.assertEqual(a, b)

class Sensitivity(unittest.TestCase):
    script = os.path.join(SENS, "scripts", "sensitivity.py")

    def test_example(self):
        rc, out, _ = run(self.script, os.path.join(SENS, "templates", "model.example.json"))
        self.assertEqual(rc, 0)
        self.assertIn("DECISION FLIPS inside the stated range for: nothing", out)

    def test_hostile_formulas_rejected_exit2(self):
        for fm in ("9**9**9**9", '__import__("os")', "(1).real", "x/0", "1+", "open('x')"):
            m = {"formula": fm, "inputs": {"x": {"base": 1, "low": 0, "high": 2}}}
            rc, _, err = run(self.script, tmp_json(m))
            self.assertEqual(rc, 2, fm); self.assertNotIn("Traceback", err)

    def test_unknown_name_and_bad_range(self):
        self.assertEqual(run(self.script, tmp_json({"formula": "y", "inputs": {"x": {"base": 1, "low": 0, "high": 2}}}))[0], 2)
        self.assertEqual(run(self.script, tmp_json({"formula": "x", "inputs": {"x": {"base": 5, "low": 0, "high": 2}}}))[0], 2)

class Regret(unittest.TestCase):
    script = os.path.join(REG, "scripts", "regret.py")

    def test_conflict_detected(self):
        rc, out, _ = run(self.script, os.path.join(REG, "templates", "decision.example.json"))
        self.assertIn("minimax-regret choice: Rent", out)
        self.assertIn("expected-value choice: Wait 12 months", out)
        self.assertIn("CONFLICT", out)

    def test_bad_input_exit2_no_traceback(self):
        for a in ("/no/such.json", tmp_json(None, raw="{bad")):
            rc, _, err = run(self.script, a)
            self.assertEqual(rc, 2); self.assertNotIn("Traceback", err)

class DebtLedger(unittest.TestCase):
    def test_ledger_decisions(self):
        rc, out, _ = run(os.path.join(DEBT, "scripts", "debt_calc.py"), "--ledger", os.path.join(DEBT, "templates", "debt.example.json"))
        self.assertEqual(out.count("PAY NOW"), 3)  # 2 rows + the summary line
        self.assertEqual(out.count("ACCEPT"), 1)
        self.assertIn("entries 3 | problems 0", out)

class Router(unittest.TestCase):
    def test_builtin_cases(self):
        rc, out, _ = run(os.path.join(ROOT, "core", "skill-router", "scripts", "route.py"), "--test")
        self.assertEqual(rc, 0, out)

class SecurityScan(unittest.TestCase):
    script = os.path.join(ROOT, "coding", "security-durability", "scripts", "scan_security.py")

    def _scan(self, text, name="x.py"):
        d = tempfile.mkdtemp(); p = os.path.join(d, name)
        with open(p, "w", encoding="utf-8") as fh: fh.write(text)
        return run(self.script, d, "--json")

    def test_finds_known_bad_patterns(self):
        code = ('API_KEY = "sk_live_abcdef123456789"\n' 'requests.get(u, verify=False)\n' 'subprocess.run(c, shell=True)\n'
                'cur.execute("SELECT * FROM t WHERE id=" + uid)\n' 'pickle.loads(b)\n')
        rc, out, _ = self._scan(code)
        ids = [r["id"] for r in json.loads(out)]
        self.assertEqual(rc, 1)
        for want in ("SEC01", "SEC02", "SEC03", "SEC04", "SEC05"):
            self.assertIn(want, ids)

    def test_compound_secret_names(self):
        for name in ("SECRET_TOKEN", "DB_PASSWORD", "STRIPE_API_KEY", "client_secret", "authToken"):
            rc, out, _ = self._scan(f'{name} = "abcd1234efgh5678"\n')
            self.assertEqual(rc, 1, name)

    def test_secret_value_is_masked(self):
        _, out, _ = self._scan('PASSWORD = "hunter2hunter2"\n')
        self.assertNotIn("hunter2hunter2", out)

    def test_clean_code_and_parameterised_sql_exit0(self):
        rc, out, _ = self._scan('cur.execute("SELECT * FROM t WHERE id=%s", (uid,))\nx = 1\n')
        self.assertEqual(rc, 0, out)

    def test_ignore_marker_and_bad_path(self):
        self.assertEqual(self._scan("requests.get(u, verify=False)  # nosec\n")[0], 0)
        self.assertEqual(run(self.script, "/no/such/dir")[0], 2)

class TestScan(unittest.TestCase):
    script = os.path.join(ROOT, "coding", "test-durability", "scripts", "scan_tests.py")

    def _scan(self, name, text):
        d = tempfile.mkdtemp(); os.makedirs(os.path.join(d, "tests"))
        with open(os.path.join(d, "tests", name), "w", encoding="utf-8") as fh: fh.write(text)
        rc, out, _ = run(self.script, d, "--json")
        return rc, json.loads(out)["findings"]

    def test_flags_rot_patterns(self):
        code = ("import time, random\nimport requests\n"
                "def test_a():\n    x = 1\n"
                "def test_b():\n    time.sleep(1)\n    assert True\n"
                "def test_c():\n    requests.get('https://x.example')\n    assert 1\n"
                "def test_d():\n    assert f('2023-05-01') == 1\n"
                "def test_e():\n    assert random.random() < 2\n")
        rc, f = self._scan("test_x.py", code)
        ids = {r["id"] for r in f}
        self.assertEqual(rc, 1)
        for want in ("TST01", "TST02", "TST03", "TST04", "TST06", "TST07"):
            self.assertIn(want, ids)

    def test_mock_heavy_file(self):
        code = "from unittest.mock import MagicMock\ndef test_a():\n    a = MagicMock(); b = MagicMock(); c = MagicMock()\n    assert a\n"
        self.assertIn("TST08", {r["id"] for r in self._scan("test_m.py", code)[1]})

    def test_clean_suite_exit0_and_bad_path(self):
        rc, f = self._scan("test_ok.py", "def test_ok():\n    assert 1 + 1 == 2\n")
        self.assertEqual((rc, f), (0, []))
        self.assertEqual(run(self.script, "/no/such/dir")[0], 2)

    def test_assertion_inside_helper_is_not_flagged(self):
        code = ("import unittest\nclass T(unittest.TestCase):\n"
                "    def check(self, x):\n        self.assertEqual(x, 1)\n"
                "    def test_a(self):\n        self.check(1)\n"
                "    def test_b(self):\n        y = 2\n")
        rc, f = self._scan("test_h.py", code)
        flagged = [r["text"] for r in f if r["id"] == "TST01"]
        self.assertEqual(flagged, ["test_b"])

    def test_non_test_files_ignored(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "app.py"), "w", encoding="utf-8") as fh: fh.write("import time\ntime.sleep(1)\n")
        self.assertEqual(run(self.script, d)[0], 0)

class LineScan(unittest.TestCase):
    script = os.path.join(ROOT, "coding", "line-durability", "scripts", "scan_line_risks.py")

    def test_unit_constants_ignored_but_magic_numbers_flagged(self):
        d = tempfile.mkdtemp()
        with open(os.path.join(d, "a.py"), "w", encoding="utf-8") as fh:
            fh.write("def f(x):\n    return x / 3600 + x * 0.1375\n")
        _, out, _ = run(self.script, d)
        self.assertIn("0.1375", out); self.assertNotIn("3600", out)

class AiCodeAudit(unittest.TestCase):
    script = os.path.join(ROOT, "coding", "ai-code-audit", "scripts", "scan_ai_risks.py")

    def _project(self, files):
        d = tempfile.mkdtemp()
        for rel, text in files.items():
            p = os.path.join(d, rel); os.makedirs(os.path.dirname(p), exist_ok=True)
            with open(p, "w", encoding="utf-8") as fh: fh.write(text)
        return d

    def test_finds_each_pattern(self):
        d = self._project({
            "requirements.txt": "requests==2.31.0\n",
            "app.py": ("import os, sys\nimport requests\nimport fancy_ai_helper\nfrom collections import OrderedDictX\n"
                       "from abc import ABC, abstractmethod\nKEY = \"YOUR_API_KEY\"\n"
                       "class Storage(ABC):\n    @abstractmethod\n    def save(self, x): ...\n"
                       "class Disk(Storage):\n    def save(self, x):\n        return os.getcwdu()\n"
                       "def process(d):\n    # rest of the code here\n    pass\n"),
            "tests/test_app.py": ("import pytest\n\ndef test_none():\n    pass\n\ndef test_true():\n    assert True\n\n"
                                  "def test_self():\n    x = 1\n    assert x == x\n\n@pytest.mark.skip\ndef test_skip():\n    assert 1 == 2\n"
                                  "\ndef test_good():\n    assert 1 + 1 == 2\n")})
        rc, out, _ = run(self.script, d, "--json")
        rows = json.loads(out); ids = {r["pattern"] for r in rows}
        self.assertEqual(rc, 1)
        for want in ("A01", "A02", "A03", "A04", "A05", "A06"):
            self.assertIn(want, ids)
        notes = " ".join(r["note"] for r in rows)
        self.assertIn("fancy_ai_helper", notes); self.assertIn("os.getcwdu", notes); self.assertIn("OrderedDictX", notes)
        self.assertNotIn("test_good", notes)          # a real test is not flagged
        self.assertNotIn("import `requests`", notes)  # declared dependency is not flagged

    def test_clean_code_exit0_and_bad_path_exit2(self):
        d = self._project({"requirements.txt": "", "ok.py": "import os\n\ndef where():\n    return os.getcwd()\n"})
        self.assertEqual(run(self.script, d)[0], 0)
        rc, _, err = run(self.script, "/no/such/path")
        self.assertEqual(rc, 2); self.assertNotIn("Traceback", err)
        self.assertEqual(run(self.script)[0], 2)

    def test_alias_and_local_imports_not_flagged(self):
        d = self._project({"requirements.txt": "PyYAML==6.0\nbeautifulsoup4\n",
                           "helpers.py": "X = 1\n",
                           "main.py": "import yaml\nimport bs4\nimport helpers\nprint(yaml, bs4, helpers)\n"})
        rc, out, _ = run(self.script, d)
        self.assertEqual(rc, 0, out)


class DiffReview(unittest.TestCase):
    script = os.path.join(ROOT, "coding", "diff-review", "scripts", "diff_stats.py")
    sample = os.path.join(ROOT, "coding", "diff-review", "templates", "sample.diff")

    def test_sample_diff_flags_and_masking(self):
        rc, out, _ = run(self.script, self.sample, "--json")
        data = json.loads(out); ids = [f["id"] for f in data["flags"]]
        self.assertEqual(rc, 1)
        for want in ("D04", "D05", "D06", "D07"):
            self.assertIn(want, ids)
        self.assertNotIn("D01", ids)                       # a test file changed
        self.assertNotIn("abcdef123456", out)              # secret value is masked
        self.assertEqual(data["total_changed_lines"], 14)

    def test_source_without_tests_and_size_flags(self):
        diff = "diff --git a/app/x.py b/app/x.py\n--- a/app/x.py\n+++ b/app/x.py\n@@ -1,1 +1,8 @@\n" + "".join(f"+line{i} = {i}\n" for i in range(8))
        rc, out, _ = run(self.script, tmp_json(None, raw=diff), "--json")
        self.assertIn("D01", [f["id"] for f in json.loads(out)["flags"]])
        rc, out, _ = run(self.script, tmp_json(None, raw=diff), "--max-lines", "3", "--json")
        self.assertIn("D02", [f["id"] for f in json.loads(out)["flags"]])

    def test_clean_diff_exit0(self):
        diff = ("diff --git a/app/x.py b/app/x.py\n--- a/app/x.py\n+++ b/app/x.py\n@@ -1,1 +1,2 @@\n a = 1\n+b = 2\n"
                "diff --git a/tests/test_x.py b/tests/test_x.py\n--- a/tests/test_x.py\n+++ b/tests/test_x.py\n@@ -1,1 +1,2 @@\n def test_a():\n+    assert b == 2\n")
        rc, out, _ = run(self.script, tmp_json(None, raw=diff))
        self.assertEqual(rc, 0, out)

    def test_bad_input_exit2_no_traceback(self):
        for args in (["/no/such/file.diff"], [tmp_json(None, raw="not a diff at all")], ["--max-lines", "x"]):
            rc, _, err = run(self.script, *args)
            self.assertEqual(rc, 2, args); self.assertNotIn("Traceback", err)

    def test_git_range(self):
        try:
            d = tempfile.mkdtemp()
            def g(*a): subprocess.run(["git", "-C", d, *a], check=True, capture_output=True)
            g("init", "-q"); g("config", "user.email", "a@b"); g("config", "user.name", "t")
            for n, text in ((1, "a = 1\n"), (2, "a = 1\nprint(a)\n")):
                with open(os.path.join(d, "m.py"), "w", encoding="utf-8") as f: f.write(text)
                g("add", "."); g("commit", "-qm", f"c{n}")
        except (OSError, subprocess.CalledProcessError):
            self.skipTest("git not available")
        r = subprocess.run([sys.executable, "-I", self.script, "--git", "HEAD~1", "--json"], cwd=d, capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stderr)
        self.assertIn("debug leftover", r.stdout)


class ApiContract(unittest.TestCase):
    script = os.path.join(ROOT, "coding", "api-contract-stability", "scripts", "contract_diff.py")
    tdir = os.path.join(ROOT, "coding", "api-contract-stability", "templates")
    old, new = os.path.join(tdir, "contract.old.example.json"), os.path.join(tdir, "contract.new.example.json")

    def test_example_pair_counts_and_exit1(self):
        rc, out, _ = run(self.script, self.old, self.new, "--json")
        data = json.loads(out)
        self.assertEqual(rc, 1)
        self.assertEqual(data["counts"], {"BREAKING": 13, "RISKY": 5, "SAFE": 4})
        notes = " ".join(c["note"] for c in data["changes"])
        for want in ("operation removed", "field removed from the response", "new required field in the request",
                     "authentication now required", "enum values added"):
            self.assertIn(want, notes)

    def test_direction_matters(self):
        old = {"type": "object", "required": ["a"], "properties": {"a": {"type": "string"}, "b": {"type": "string"}}}
        new = {"type": "object", "required": ["a", "c"], "properties": {"a": {"type": "string"}, "c": {"type": "string"}}}
        req = run(self.script, tmp_json(old), tmp_json(new), "--mode", "request", "--json")[1]
        resp = run(self.script, tmp_json(old), tmp_json(new), "--mode", "response", "--json")[1]
        lv = lambda out, where: {c["level"] for c in json.loads(out)["changes"] if c["where"] == where}
        self.assertEqual(lv(req, "$.c"), {"BREAKING"})   # new required request field breaks senders
        self.assertEqual(lv(req, "$.b"), {"RISKY"})      # removed request field: only risky
        self.assertEqual(lv(resp, "$.c"), {"SAFE"})      # new response field is harmless
        self.assertEqual(lv(resp, "$.b"), {"BREAKING"})  # removed response field breaks readers

    def test_identical_exit0_and_bad_inputs_exit2(self):
        self.assertEqual(run(self.script, self.old, self.old)[0], 0)
        for args in ([tmp_json(None, raw="{bad"), self.new], ["/no/such.json", self.new], [self.old],
                     [tmp_json({"swagger": "2.0", "paths": {}}), self.new], [self.old, self.new, "--mode", "sideways"]):
            rc, _, err = run(self.script, *args)
            self.assertEqual(rc, 2, args); self.assertNotIn("Traceback", err)

    def test_ref_cycle_does_not_hang(self):
        doc = {"$ref": "#/$defs/N", "$defs": {"N": {"type": "object", "properties": {"next": {"$ref": "#/$defs/N"}, "v": {"type": "string"}}}}}
        self.assertEqual(run(self.script, tmp_json(doc), tmp_json(doc))[0], 0)


class Repo(unittest.TestCase):
    def test_validator(self):
        rc, out, _ = run(os.path.join(ROOT, "tools", "validate_repo.py"))
        self.assertEqual(rc, 0, out)

    def test_other_scripts_fail_clean_on_bad_input(self):
        scripts = ["finance/tail-risk-review/scripts/tail_stats.py", "coding/fitness-functions/scripts/check_rules.py",
                   "coding/adr-writer/scripts/adr_lint.py", "core/calibration-loop/scripts/calibration_report.py",
                   "coding/ai-code-audit/scripts/scan_ai_risks.py", "coding/diff-review/scripts/diff_stats.py"]
        for s in scripts:
            rc, _, err = run(os.path.join(ROOT, s), "/no/such/path.json")
            self.assertNotEqual(rc, 0, s); self.assertNotIn("Traceback", err, s)

class Miner(unittest.TestCase):
    """v2 miner: positives come from git blame, not from 'same file'; housekeeping commits are ignored."""
    def _repo(self, commits):
        d = tempfile.mkdtemp()
        def g(*a, env=None):
            subprocess.run(["git", "-C", d, *a], check=True, capture_output=True, env=env)
        g("init", "-q"); g("config", "user.email", "a@b"); g("config", "user.name", "t")
        for msg, day, content in commits:
            with open(os.path.join(d, "m.py"), "w", encoding="utf-8") as f:
                f.write(content)
            date = f"2025-01-{day:02d}T10:00:00"
            g("add", "."); g("commit", "-qm", msg, env=dict(os.environ, GIT_AUTHOR_DATE=date, GIT_COMMITTER_DATE=date))
        return d

    def _mine(self, repo):
        out = tempfile.mkdtemp()
        rc, _, err = run(os.path.join(ROOT, "benchmarks/git-history-miner/miner.py"), repo, "--out", out, "--clean-days", "1")
        self.assertEqual(rc, 0, err)
        return {c["subject"]: c for c in (json.load(open(os.path.join(out, f), encoding="utf-8")) for f in os.listdir(out))}

    A = "def f(x):\n    a = x + 1\n    b = a * 2\n    return b\n"
    G = "\ndef g(y):\n    p = y - 1\n    q = p * 3\n    return q\n"

    def test_unrelated_fix_in_same_file_is_not_positive(self):
        cases = self._mine(self._repo([("init", 1, "X = 1\n"), ("add f", 2, self.A), ("add g", 3, self.A + self.G),
                                       ("fix bug in g", 4, (self.A + self.G).replace("p * 3", "p * 4"))]))
        self.assertEqual(cases["add g"]["label"], "positive")
        self.assertNotIn("add f", [s for s, c in cases.items() if c["label"] == "positive"])

    def test_housekeeping_commit_is_never_a_case(self):
        cases = self._mine(self._repo([("init", 1, "X = 1\n"), ("add f", 2, self.A), ("This is 2.0-dev", 3, self.A + self.G),
                                       ("fix bug", 4, (self.A + self.G).replace("p * 3", "p * 4"))]))
        self.assertNotIn("This is 2.0-dev", cases)


class OrderTotalGaps(unittest.TestCase):
    """Gaps found by running the process on an order-total function: http endpoint, no timeout, float money."""
    def _scan(self, script, code, *args):
        d = tempfile.mkdtemp(); p = os.path.join(d, "orders.py")
        with open(p, "w", encoding="utf-8") as f: f.write(code)
        return run(os.path.join(ROOT, script), p, *args)[1]

    BAD = ("import requests\ndef t(items):\n    total = 0\n    for it in items:\n        total += it['price'] * it['qty']\n"
           "    total = total * 1.1\n    r = requests.get('http://api.partner.com/rates')\n    return total\n")
    GOOD = ("import requests\nfrom decimal import Decimal\ndef t(items):\n    total = Decimal(0)\n    for it in items:\n"
            "        total += Decimal(it['price']) * it['qty']\n    r = requests.get('https://api.partner.com/rates', timeout=5)\n"
            "    l = requests.get('http://localhost:8000/x', timeout=5)\n    return total\n")

    def test_plain_http_is_flagged_but_https_and_loopback_are_not(self):
        self.assertIn("SEC10", self._scan("coding/security-durability/scripts/scan_security.py", self.BAD))
        self.assertNotIn("SEC10", self._scan("coding/security-durability/scripts/scan_security.py", self.GOOD))

    def test_missing_timeout_and_float_money_are_flagged(self):
        out = self._scan("coding/line-durability/scripts/scan_line_risks.py", self.BAD)
        self.assertIn("network call without timeout", out); self.assertIn("M12", out)
        self.assertEqual(out.count("[M12]"), 1)  # one finding per line, no duplicate

    def test_clean_code_has_no_new_findings(self):
        out = self._scan("coding/line-durability/scripts/scan_line_risks.py", self.GOOD)
        self.assertNotIn("M12", out); self.assertNotIn("without timeout", out)


if __name__ == "__main__":
    unittest.main(verbosity=1)
