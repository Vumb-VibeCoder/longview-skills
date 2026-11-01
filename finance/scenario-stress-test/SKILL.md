---
name: scenario-stress-test
description: Answer 'what if income drops', 'can we survive a bad year', 'how long is our runway if revenue falls' questions. Stress a financial plan or model against named adverse scenarios (income drop, cost spike, delayed revenue, rate or price shock, simultaneous bad events) and report where it breaks, in which month and by how much. Use before committing to a budget, loan, investment or business plan. Ships cashflow.py, which applies scenario overrides to a base model and exits non-zero when a must-survive scenario fails.
metadata:
  domain: finance
  status: READY
---
# Scenario Stress Test: find the breaking point before reality does

Averages tell you the plan works when nothing goes wrong. This skill asks what goes wrong, and how much slack there is.

## When to activate
Before committing money or time to a plan with fixed obligations (rent, loan payments, payroll, subscriptions) and uncertain inflows. Run `horizon-fit` first.

## Procedure
1. **Build or request the base model** (see `long-horizon-cashflow` for the fields). Make sure fixed obligations are separated from flexible spending; that separation is what decides whether a shock is survivable.
2. **Choose scenarios from the change drivers, not from imagination.** For each of: income, main cost, timing, and external rate or price, write one moderate and one severe case. Use `change-vectors` to find what actually moves in this domain. Severe means severe: a 40-100% income loss, not 5%.
3. **Always include a correlated scenario:** two bad things at the same time (job loss plus a large repair; revenue delay plus a rate rise). Real shocks cluster; a test of one-at-a-time shocks overstates safety.
4. **Add a reverse stress test:** for the one input that matters most, find the value at which the plan fails. Use `assumption-sensitivity` break-even for this. A plan that fails at "income minus 8%" is fragile; one that fails at "income minus 60%" has margin.
5. **Run:** put the scenarios in the model's `scenarios` list and run `python scripts/cashflow.py model.json`. Each scenario overrides base fields (`income_shock`, `income_shock_from_month`, `inflation_annual`, `expense_growth_annual`, `add_one_offs`, ...). Mark scenarios you accept failing with `"must_survive": false` and say why in the report.
6. **Classify the result per scenario:** SURVIVES (never below the floor), SURVIVES NARROWLY (lowest balance under 3 months of expenses), FAILS at month N.
7. **For every failure name the mitigation and what it costs:** buffer size, a credit line (with its terms), a way to cut fixed obligations, a trigger to act early. Re-run to confirm the mitigation actually fixes it. Unverified mitigations count as none.
8. Feed the surviving-narrowly and failing scenarios into `assumption-tripwires` so the early-warning signal exists before the shock.

## Mandatory questions
- Which fixed obligation turns a temporary shock into a permanent problem?
- How many months do we have between the first warning sign and running out?
- Is there any scenario we refused to test because the answer was unpleasant?

## Output
A table of scenarios with result and lowest balance and month, the reverse-stress break value, the verified mitigations, and the explicit list of accepted failures with their rationale.

## Limits
Scenarios are chosen by a person, so the test only covers what was imagined. It does not give probabilities; for the extreme tail use `tail-risk-review`. This is a planning tool, not financial advice.
