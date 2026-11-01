---
name: tail-risk-review
description: Answer 'could this wipe me out', 'how bad can drawdown get', 'is my portfolio too leveraged' questions. Review ruin and extreme-loss risk that averages and normal-distribution models hide - worst observed periods, expected shortfall, drawdown, sample-length limits, leverage, concentration and correlation under stress. Use for any investment, portfolio, position-sizing or business exposure where a single bad event could be unrecoverable. Ships tail_stats.py (empirical VaR/CVaR vs a normal model, drawdown, fat-tail and short-sample flags).
metadata:
  domain: finance
  status: READY
---
# Tail Risk Review: can one bad period end the game?

The question is not "what is the average outcome" but "is there an outcome I cannot recover from, and how close am I to it?" Survival comes first; returns second.

## When to activate
Any exposure with potential for large loss: investments, leverage, concentrated positions, a business that depends on one customer or supplier, guarantees, short options, an emergency fund that is too small. Run `horizon-fit` first; failure cost F of money/safety makes this class C or D.

## Procedure
1. **Define ruin concretely** before any number: the loss that cannot be recovered or that forces a bad action (margin call, missed payment, shutdown). Write it as a figure or percentage. A review with no ruin line is just statistics.
2. **Collect the loss history** as periodic returns (decimals), as long a series as exists, and say its length and the worst event it contains. Run `python scripts/tail_stats.py returns.json`.
3. **Judge by the tail, not by VaR.** Look at: worst periods and how many sd below the mean they are, CVaR (average loss in the worst tail), max drawdown, and the CVaR ratio against the normal model. A ratio above about 1.3 or excess kurtosis above 1 means the bell curve understates the tail. VaR at 95% can look fine while the tail is terrible; do not use it alone.
4. **Respect sample length.** With fewer than about 60 observations, or a history that never included a crisis, the worst observed loss is a LOWER bound. Say so, and add a stress figure from a documented historical or hypothetical shock rather than extrapolating.
5. **Check the multipliers that turn bad into ruin:** leverage (a 20% drop on 5x leverage is total loss), concentration (one asset, customer or counterparty above 25-30% of exposure), liquidity (can you exit, and at what discount, when everyone else does?), and correlation (assets that diversify in calm periods often fall together in stress; assume correlation moves toward 1 in the stress case).
6. **Apply the ruin test:** exposure x plausible worst loss, versus the ruin line. If one plausible event (use the worst observed loss multiplied by 1.5 as a cheap stand-in for the unobserved) crosses the ruin line, the position is too large regardless of its expected return.
7. **Fix by shrinking the exposure or capping the loss, not by hoping:** smaller position, no leverage, stop or hedge with known cost, diversified counterparties, a larger cash buffer. State the cost of the fix (lost upside) so the trade-off is explicit; take it to `reversibility-check` if the position cannot be exited cheaply.
8. Put the ruin line and the monitored trigger (drawdown level, concentration ceiling) into `assumption-tripwires`.

## Mandatory questions
- What exact loss is unrecoverable?
- How long is the history, and did it include a crisis?
- Does anything here multiply a loss (leverage, concentration, illiquidity, correlation)?

## Output
Ruin line, tail statistics with their flags, the stress case, the multiplier check, the ruin-test result (PASS / FAIL) and the smallest change that makes it pass. If a full score is needed use `verdict-format` (Cost of failure and Reversibility carry the most weight here).

## Exit path
- **Missing input:** fewer than 10 observations or no leverage figures: ask for more data and do not estimate tail loss.
- **Script problem:** if `tail_stats.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** if the person describes distress or an urgent loss, answer the immediate question and suggest a qualified adviser.

## Limits
Historical statistics describe the past; a regime that never occurred is not in the data. Normal-model comparisons use fixed z-values for common alphas only (0.01, 0.025, 0.05, 0.10). This is a risk-screening aid, not investment advice or a guarantee of safety.
