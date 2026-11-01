---
name: assumption-sensitivity
description: Answer 'is this worth it', 'which number matters most', 'what is the break-even' questions. Rank which assumptions drive a numeric conclusion and find the exact value of each that flips the decision (break-even), so attention goes to the 1-2 inputs that matter. Use for business cases, ROI, pricing, buy-vs-rent or any model where the answer depends on uncertain inputs. Ships sensitivity.py, a safe formula evaluator with swing ranking and bisection break-evens.
metadata:
  domain: finance
  status: READY
---
# Assumption Sensitivity: which guess actually matters?

Most models have 10 inputs but 1-2 drive the answer. Debating the other eight is wasted effort; being wrong on the top one is the whole risk.

## When to activate
A decision rests on a calculation with uncertain inputs. Run `horizon-fit` first. Pair with `assumption-ledger`: every input here is an assumption and needs a confidence and an owner.

## Procedure
1. **Write the output as a formula** with a single decision threshold (profit >= 0, ROI >= hurdle, runway >= 12 months). If there is no threshold, define one first: "what result would change what we do?"
2. **For each input give base, low and high.** Low and high must be a defensible range (roughly the 10th and 90th percentile of your belief), not an arbitrary plus/minus 10%. If you cannot defend a range, the input is `confidence: GUESS` in the ledger.
3. **Run:** `python scripts/sensitivity.py model.json`. It evaluates the formula safely (arithmetic and min/max/abs/sqrt/log/exp only; anything else is rejected), ranks inputs by output swing, and bisects the break-even value of each input within 5x its base.
4. **Read three things:** (a) the ranking: the top two inputs are the ones to research, (b) `flip-in-range = YES`: the decision flips inside your own stated range, so the conclusion is not supported by current knowledge, (c) the break-even relative to base: a break-even only 10% away from base is a fragile conclusion even if the range says "no flip".
5. **If an input flips the decision:** the next action is to reduce uncertainty on that input (data, quote, pilot), or to choose the option that is robust to it, not to refine the other inputs.
6. **Check combinations manually** for the top two or three inputs (set several to their low values together and re-run). The script is one-at-a-time and says so; interacting bad cases are where plans die.
7. Record break-evens as tripwires: "if actual price falls below 20, the case no longer holds" is a check that can be monitored (`assumption-tripwires`).

## Mandatory questions
- Which input, if wrong by its stated range, flips the answer?
- How far from base is each break-even, in percent?
- What would we need to see to move this input from GUESS to MEASURED?

## Output
The ranked table, the flipping inputs, the break-even list with distance from base, the combined-low check, and the single research action with the highest value.

## Limits
Linear scanning of independent inputs; correlations between inputs are ignored. The formula is only as good as its structure: a missing term (a cost nobody listed) is invisible to this skill, so ask for it explicitly. Not financial advice.
