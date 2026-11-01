---
name: long-horizon-cashflow
description: Answer any 'will the money last', 'how long will my savings last', runway, retirement-withdrawal or budget-over-years question. Project cash over years with explicit real-vs-nominal handling, expense growth tied to inflation, lumpy one-off costs and a survival test under named shocks. Use for budgets, runway, retirement or business cashflow plans, and any "will the money last" question. Ships cashflow.py (scenario projection, exits non-zero when a must-survive scenario runs out of cash) and an example model.
metadata:
  domain: finance
  status: READY
---
# Long-Horizon Cashflow: will the money last?

A flat average hides the two things that actually end plans: **lumpy costs** and **a bad stretch early on**. This skill makes both visible.

## When to activate
Any plan where money flows over more than about 12 months: runway, savings goal, retirement, a business forecast, a loan or purchase decision. Run `horizon-fit` first (a one-off purchase under three months is class A/B: just do the arithmetic).

## Required inputs (ask, or state the assumption AND label it as an assumption)
Starting cash; monthly income and expenses; horizon in months; expected income growth; inflation; known lumpy items (repairs, replacements, taxes, tuition) with month and amount; the cash floor below which the plan counts as failed (default 0).

## Procedure
1. **Separate nominal from real.** Output both. Any statement about purchasing power must use the real figure. If inflation is unknown, run 2% and 8% and say which you used.
2. **Tie expenses to inflation by default.** Expenses grow with inflation unless you have a reason. Income does NOT automatically keep pace; set its growth explicitly. A plan where income grows slower than expenses is shrinking even if the balance rises today.
3. **List lumpy costs separately** as one-offs with a month. Replacement cycles of equipment, vehicles, roofs, devices, insurance renewals and taxes belong here, not inside the monthly average. If none were named, ask; a plan with zero one-offs over 3+ years is almost always incomplete.
4. **Define the survival test before the numbers:** at least three named shocks, each a concrete change to the model (for example income falls 40% from month 12, inflation 9%, income stops for 6 months plus a 5,000 repair). Mark which must be survived (`must_survive`, default true) and which are only informational.
5. **Run it:** `python scripts/cashflow.py model.json`. For savings or retirement questions set `return_annual` together with `return_compounding`, and `expense_indexing: annual_step` for withdrawals raised once a year (see `templates/retirement.example.json`; it deliberately exits 1 because the 3%-indexed scenario is marked must_survive and runs out of cash in month 250, while the lower-returns scenario is informational only). It prints final nominal and real balance, the lowest balance and its month, and the first month cash goes negative, for the base case and each scenario. Exit code 1 means a must-survive scenario ran out of cash.
6. **Read the result by the minimum, not the end.** A plan that ends positive but dips below the floor in month 14 has failed at month 14. Report the lowest point and its month first.
7. **If a scenario fails, give the smallest lever that fixes it** (a buffer of X, cutting Y, delaying one-off Z) and re-run to confirm. Do not propose a lever you have not re-run. For a reverse-stress threshold ("spend at most X", "start with at least Y"), search for the boundary, round it in the safe direction (spending down, starting balance up), then re-run at the exact number you will print and confirm the scenario ends at or above the floor. A threshold that still ends below the floor by even one unit is wrong; print the margin left at the final month.
8. Record the growth, inflation and shock assumptions in `assumption-ledger`; attach a tripwire to the ones that matter (for example "if monthly expenses exceed X for 2 months, re-run").

## Conventions to state in every answer
- Compounding: monthly at rate/12, or effective annual converted to a monthly rate. The two differ by several percent over 30 years; name the one used.
- Withdrawals: fixed in nominal dollars, or indexed to inflation. Always show both when the user did not say.
- Real vs nominal: report the real balance next to the nominal one.
- Not modelled: taxes, fees, return volatility and sequence risk. Say so, and run a bad-early-years shock (for example returns 2 points lower for the first 5 years) when you can.
- If no shell exists, write `NOT MEASURED: scripts/cashflow.py` and give closed-form bounds; never present estimates as script output.

## Mandatory questions
- What is the lowest balance, and in which month?
- What changes if income starts one year late?
- Which one-off is missing from this model?

## Output
The scenario table, the survival result, the single biggest vulnerability, the smallest verified fix, and the assumptions that must be re-checked. For an overall judgment use `verdict-format`, mapping: Cost of failure = depth of the worst surviving-scenario dip; Assumption fragility = how many growth/inflation inputs are unrecorded.

## Exit path
- **Missing input:** start cash, income, spending or horizon missing: ask for each; do not assume.
- **Script problem:** if `cashflow.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** for anything that looks like advice on investments, tax or law, give the projection and the disclaimer, not a recommendation.

## Limits
Deterministic scenarios, not probabilities. Monthly steps ignore intra-month timing. Investment return is modelled only as a constant `return_annual` on a positive balance; no taxes, fees, volatility or sequence risk (run a lower-return scenario instead). This is arithmetic for decisions, not financial advice; a licensed advisor should review large commitments.
