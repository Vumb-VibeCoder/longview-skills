---
name: decision-regret-check
description: Answer 'buy or wait', 'big bet or small bet' questions. Compare options across scenarios by regret (how much worse than the best choice in hindsight), worst case and expected value, and expose when they disagree. Use for hard personal, financial or business choices under uncertainty (buy vs wait, commit vs keep options open, big vs small bet). Ships regret.py (regret matrix, minimax regret, maximin, expected value, dominated options).
metadata:
  domain: finance
  status: READY
---
# Decision Regret Check: choose the option you can live with in every scenario

Expected value ignores that some losses are survivable and others are not. Regret analysis asks: across the futures that could happen, which option never leaves me far from the best I could have done?

## When to activate
A choice between 2-5 concrete options where the future is uncertain and the downside differs a lot between options. Run `horizon-fit` first. Skip for tiny, reversible choices (class A/B): just decide.

## Procedure
1. **List real options, including "wait" and "do the smaller version".** If only two options exist because the question was framed that way, add a third that buys information or keeps the door open (`reversibility-check`).
2. **List 3-5 scenarios that differ in what matters** (not three flavours of "it goes fine"). Include a bad one, a middling one, a good one. Scenarios must be mutually exclusive and cover what you consider plausible.
3. **Fill the payoff matrix** in one unit (money, or a 0-100 utility score): outcome of each option in each scenario, including costs of carrying the option and of undoing it. A blank cell is not allowed; if you cannot estimate it, that is the uncertainty to resolve first.
4. **Assign probabilities only if you can defend them.** If not, leave them out; the tool then reports only worst case and regret, which is the honest result. Never invent precise probabilities to get an expected value.
5. **Run:** `python scripts/regret.py decision.json`. It reports per option: worst case, maximum regret, expected value (if probabilities given), the minimax-regret choice, the maximin choice, and dominated options.
6. **Read it in this order:** (a) remove dominated options, (b) if minimax regret, maximin and expected value agree, decide with confidence, (c) if they disagree, the script prints CONFLICT: this is a question of values, not arithmetic. Ask what loss you cannot absorb; if one scenario is unrecoverable (see `tail-risk-review`), maximin or minimax regret wins over expected value.
7. **Test the decision's sensitivity:** change the most uncertain payoff or probability by a plausible amount and re-run. If the chosen option changes, say which number it hinges on and go measure that (`assumption-sensitivity`).
8. **Pre-commit the review point:** the date or event at which you will re-decide, and what you would have to see. Record as a tripwire.

## Mandatory questions
- Which scenario is unrecoverable, and which option is exposed to it?
- Would I still endorse this choice if the worst plausible scenario happened?
- What cheap action would reveal which scenario we are in?

## Output
The matrix with regrets, the three rule results, any CONFLICT with the deciding consideration stated, the sensitivity result, and the review trigger.

## Exit path
- **Missing input:** payoffs or scenario probabilities missing: ask, or run with equal weights and say so.
- **Script problem:** if `regret.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** if expected value and minimax regret disagree, show both and ask which loss the person cannot absorb.

## Limits
The result is only as good as the scenarios and payoffs; the tool cannot see an option or scenario you did not list. Regret and expected value are different value systems, so the skill reports both instead of choosing for you. Not financial or legal advice.
