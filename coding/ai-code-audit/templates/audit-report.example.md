# AI code audit: example report

Request given to the AI: "add a function that loads orders and totals them".
Scope: `app.py`, `tests/test_app.py` (2 files). Class: C (money involved).

Scan: `python scripts/scan_ai_risks.py .` -> 17 candidates, 11 confirmed, 6 discarded
(4 unused imports left by an abandoned approach were confirmed as A06 and counted once below; the pytest import was a false positive: pytest is a dev dependency not listed in requirements.txt).

| Location | Pattern | Evidence | Severity | Smallest fix |
|---|---|---|---|---|
| app.py:16 | A02 | `os.getcwdu` does not exist in Python 3; it only ran on an error path nobody exercised | MUST FIX | Use `os.getcwd()` and add a test that reaches the line |
| app.py:23 | A02 | `sys.exit_now` is not a function of `sys` | MUST FIX | Use `sys.exit()` or return a value |
| app.py:4 | A01 | `fancy_ai_helper` is not declared, not installed and not in the repo | MUST FIX | Remove; the function body does not need it |
| app.py:18 | A03 | `process` has the body `pass` and a comment "rest of the code here"; callers treat it as working | MUST FIX | Implement it or raise NotImplementedError and record it in `debt-ledger` |
| app.py:8 | A03 | `KEY = "YOUR_API_KEY"` template secret in code | SHOULD FIX | Read from the environment (see `security-durability`) |
| app.py:10 | A05 | `Storage` abstract class with one subclass and no named second use | SHOULD FIX | Inline `DiskStorage` |
| tests/test_app.py:4 | A04 | `test_no_assert` passes unless the code crashes | MUST FIX | Assert on the returned total |
| tests/test_app.py:8 | A04 | `assert True` | MUST FIX | Delete or replace with a real check |
| tests/test_app.py:15 | A04 | `test_skipped` is skipped | SHOULD FIX | Fix and enable, or delete with a note |

Verified by running: `python -m pytest -q` -> `Not run.` (pytest is not installed in this environment).
Break check (step 5): not done, no runnable tests.
Not examined: behaviour of `load()` against real order data; third-party method names (none used).
Hand-offs: `security-durability` for the template secret, `line-durability` for the rest of `app.py`.
