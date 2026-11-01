# Test plan: billing module

Class: D. Reviewed: 2026-01-20. Suite run time: 48 s (target under 60 s). Run 3 times, once reversed: stable.

## What matters most
| Behaviour | Test | Seen failing? |
|---|---|---|
| Tax is 10 percent of the subtotal | `test_tax_rate` | yes (flipped the rate, test went red) |
| Refund never exceeds the amount paid | none | n/a: **gap** |
| Invoice total is rounded half up to 2 decimals | `test_rounding` | yes |
| Currency conversion uses the stored rate | `test_convert` | no: **never checked** |

## Ageing risks found
| Where | Problem | Fix | Owner |
|---|---|---|---|
| `test_due_date` | hard-coded 2024-03-01 | pass the date in, freeze the clock | backend |
| `test_fx_live` | calls the live rates API | replace with a recorded response | backend |

## Skipped tests
| Test | Skipped since | Reason | Owner | Decide by |
|---|---|---|---|---|
| `test_legacy_import` | 2025-06-10 | importer under rewrite | data team | 2026-03-31 |

## Plan, in order
1. Add the refund test (largest money gap).
2. Fix the two ageing risks.
3. Prove `test_convert` can fail, or rewrite it.
4. Add "no sleep in tests" as a CI rule.
