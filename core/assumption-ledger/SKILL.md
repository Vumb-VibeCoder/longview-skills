---
name: assumption-ledger
description: Build a ledger of the assumptions a design, code, plan or model silently depends on, each with evidence, confidence and impact-if-wrong. Use at the start of a design, before a long-term decision, when a result looks too certain, or when asked "what are we assuming?". Feeds assumption-tripwires. Ships a JSON example ledger.
metadata:
  domain: core
  status: READY
---
# Assumption Ledger: what are we silently betting on?

Most short-sightedness is an **unspoken assumption** that was never examined. The ledger makes each one visible, rated and ownable.

## When to activate
After `horizon-fit` returns class C/D (or an escalated component). Also whenever a conclusion feels too certain. Class A/B with no escalator: skip.

## Procedure
1. **Harvest** assumptions by reading the code/design/model and walking this checklist, citing where each appears:
   data volume and shape; number of users; ordering and timing; input formats; encodings, time zones, currencies, locales; external APIs and their versions; runtime/OS/environment; libraries and their behaviour; people (who maintains it, who knows it); laws and regulations; prices, rates, costs (finance); "this will never be called with X".
2. **Invert to find hidden ones:** ask "what would have to be true for this to work?" for each core step, and "what does this code do when that is false?".
3. **Write one entry per assumption** (fields below). One sentence, falsifiable. Split compound assumptions.
4. **Rate confidence** (use the definitions, do not improvise):
   - `VERIFIED`: checked against a real artifact within the expiry window (cite it)
   - `BELIEVED`: plausible, stated by someone or inferred, not checked
   - `GUESSED`: invented to make progress
5. **Rate impact if wrong:** `HIGH` = money, data, safety or a rewrite; `MEDIUM` = a multi-day fix; `LOW` = minor, local, quickly noticed.
6. **Set expiry:** at most 12 months; at most 6 for fast-moving domains (see `horizon-fit` churn). VERIFIED entries expire too: facts decay.
7. **Route:** a tripwire is **required** when impact=HIGH and confidence is not VERIFIED, or impact=MEDIUM and confidence=GUESSED. Hand those entries to `assumption-tripwires`. The rest stay in the ledger with their expiry.
8. **Cheapest first:** for GUESSED/BELIEVED HIGH-impact entries, say what single check would turn them into VERIFIED, and do it if it costs less than an hour.

## Entry fields
`id, assumption, evidence, confidence, impact, expires (YYYY-MM-DD), owner` (+ tripwire fields `check, check_command, threshold, on_trigger` when required). See `templates/assumptions.example.json`.

## Mandatory questions
- What is true *today* that we treat as always true?
- Which assumption exists only to make the code work?
- Which assumption would nobody notice if it broke?

## Failure patterns
| Pattern | Example |
|---|---|
| Fixed scale | iterating a whole list assuming < 1,000 items |
| Fixed environment | hard-coded Windows path |
| Static partner | calling an unversioned API with no handling of format change |
| Extended present | finance model assuming today's interest rate persists |
| Unowned assumption | entry with no owner: nobody will ever re-verify it |

## Output
The ledger as JSON (template format) plus a short table of the HIGH-impact entries and which ones need tripwires.

## Exit path
- **Missing input:** nothing to analyse: ask what the design, plan or code is.
- **Stop or hand off:** if every assumption is low impact, say so and stop; a long ledger is not the goal.

## Limits
Finds only assumptions visible in the material and the model's knowledge. Assumptions about things it does not know exist are invisible: ask a domain owner to review the ledger.
