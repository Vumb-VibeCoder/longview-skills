# Worked example: what the skills make an AI do

Request: *"Write a function that computes an order total and charges the customer."*
Below is the sequence the skills prescribe for the code in `/tmp/ex/shop/billing.py` (15 lines, shown at the end).
Lines marked **[measured]** are real script output; lines marked **[judgment]** are reasoning that follows the skill's rules and should be checked by a person.

## Step 1: `horizon-fit` [judgment]
Inputs: lifetime more than 3 months (it is the checkout path), real customers exist, failure cost includes **money**.
Rule: "F includes money, so components touching that risk are at least class C." Result: **class C** (escalated). Had the request been "rename these 20 files once", the result would be class A and the verdict **TEMPORARY IS ENOUGH**: make it correct, note its debt, stop. No ledger, no council, no scoring.

## Step 2: `line-durability` scan [measured]
`python coding/line-durability/scripts/scan_line_risks.py shop/`
```
billing.py:8   [M01]  hard-coded number 1.1
billing.py:10  [M01]  hard-coded number 1.19
billing.py:12  [M01]  hard-coded URL/path http://payments.internal:8080/charge
billing.py:13  [M03]  bare except (catches everything, including KeyboardInterrupt)
1 files, 4 candidates: {'M01': 3, 'M03': 1}
```
The scanner output is a list of **candidates**; each must be confirmed against the "Do NOT flag when" column of `myopia-patterns`. All four hold here: the rates are not true constants, and the `except` swallows a payment failure.

## Step 3: what the scanner cannot see [judgment]
- M02/M11: country rules are an `if/elif` chain, so every new country edits this function; tax rates are assumed to stay fixed (extended present).
- Money is a float, the currency is fixed to USD, and nothing makes the charge safe to retry. If the request times out and is retried, the customer may be charged twice; if the exception is swallowed, they may not be charged at all.
- The function mixes pricing and payment (M08: do-everything function), so tax logic cannot be tested without the network.

## Step 4: `assumption-ledger` [judgment]
| id | assumption | confidence | impact | tripwire idea |
|---|---|---|---|---|
| A1 | VAT is 10% in VN and 19% in DE | GUESS | HIGH | rates come from a dated table; fail the build if a rate is older than its expiry |
| A2 | all prices are USD | GUESS | HIGH | assert one currency per order; reject mixed carts |
| A3 | the payment call succeeds or the caller sees the error | UNVERIFIED | HIGH | test that a failing payment service raises |

## Step 5: `verdict-format` [judgment, scores follow the rubric]
| Dimension | Score | Evidence |
|---|---|---|
| Change tolerance | 1 | a new country or rate edits this function (billing.py:7-10) |
| Coupling | 1 | pricing and the payment call share one function (billing.py:12) |
| Reversibility | 3 | one small function, a revert is cheap |
| Assumption fragility | 0 | rates and currency hard-coded with no source or expiry (billing.py:8,10,12) |
| Operability | 0 | bare `except: pass` hides failures; no tests (billing.py:13) |
| Cost of failure | 0 | a swallowed payment failure loses money |

Decision rule, first match wins: class is C (not A/B); no dimension is `NO EVIDENCE`; total = **5/18, which is <= 8**, so rule 3 applies.

```
VERDICT: REWRITE (5/18) | Class: C | Headline horizon: 1 year
Smallest fix worth doing: split pricing from payment, load rates from a dated table, use Decimal, let payment errors surface
  (lifts Change tolerance, Assumption fragility, Operability, Cost of failure)
Unknowns: how many callers use total_price(); whether the payment service is idempotent
```
"REWRITE" applies to the unit under review. For a 15-line function that is about an hour of work, which is why the skills always name the **smallest fix** next to the verdict.

## The reviewed code
```python
import requests

def total_price(items, country):
    total = 0
    for it in items:
        total += it["price"] * it["qty"]
    if country == "VN":
        total = total * 1.1          # VAT
    elif country == "DE":
        total = total * 1.19
    try:
        r = requests.post("http://payments.internal:8080/charge", json={"amount": total, "currency": "USD"})
    except:
        pass
    return total
```

## What this example does and does not show
It shows the **procedure**: classify, measure, record assumptions, score with evidence, state the smallest fix. It does not prove the procedure makes AI reviews more accurate; that needs `benchmarks/` on a repo with real history.
