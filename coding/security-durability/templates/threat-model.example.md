# Threat model: invoice upload service

Class: D (public endpoint, customer files, payments data nearby). Reviewed: 2026-01-15.

## What we protect
Customer invoices (personal and financial data), the API token for the payment provider, the admin panel.

## Entry points
| Entry | Who can reach it | Untrusted input | Checks in place |
|---|---|---|---|
| `POST /upload` | any logged-in customer | file name, file body, size | type allow-list, 10 MB limit, stored outside web root, random name |
| `GET /invoice/{id}` | any logged-in customer | `id` | owner check on the server |
| Payment webhook | payment provider | whole body | signature verified |
| Admin panel | staff on VPN | all forms | SSO, role check |

## Secrets
| Secret | Where it lives | Who rotates | Last rotated |
|---|---|---|---|
| Payment API token | secret store | platform team | 2025-11-02 |

## Worst case by actor
- Anonymous visitor: can only see the login page.
- Logged-in customer: could read another customer's invoice if the owner check is missing. **Open risk: no automated test for this.**
- Leaked payment token: refunds and customer data readable. Rotation takes about 10 minutes.

## Data kept
Invoices: kept 7 years for tax reasons, deleted by a monthly job, readable by the owner and the finance role.

## Open risks (recorded in the debt ledger)
| Risk | Owner | Re-check |
|---|---|---|
| No test for cross-customer access | backend lead | 2026-03-01 |
