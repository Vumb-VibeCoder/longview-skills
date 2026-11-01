# Rollback plan: rename `orders.total` to `orders.amount_total`

Class: C. Restore point: tag `pre-amount-total` and a database snapshot taken before step 1.

| Step | Change | Restore point | Way back | Trigger | Point of no return |
|---|---|---|---|---|---|
| 1 | Add column `amount_total`, nullable | snapshot | drop the new column | migration fails or locks the table for more than 30 s | none |
| 2 | Backfill `amount_total` from `total` in batches | snapshot | truncate the new column; `total` is untouched | row count or sum differs from `total` | none |
| 3 | Write both columns from the app (flag `dual_write`) | previous release kept | turn the flag off | error rate above baseline for 10 minutes | none |
| 4 | Read from `amount_total` (flag `read_new`) | flag off | turn the flag off | any mismatch in the shadow comparison | none |
| 5 | After 14 quiet days, drop `total` | snapshot kept 30 days | restore the column from the snapshot | n/a | `ONE-WAY: dropping `total` loses writes made after the snapshot |

Rehearsal: steps 1 to 4 reversed on a copy of production data on 2026-01-12, all passed.
Approval needed for step 5: yes, from the data owner.
