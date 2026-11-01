---
name: change-vectors
description: Identify what is most likely to change (requirements, scale, data, libraries, partners, regulation, team, environment, cost) and decide where flexibility is worth building. Use before choosing a design so flexibility goes only where change is likely and expensive. Feeds council-protocol and change-injection.
metadata:
  domain: core
  status: READY
---
# Change Vectors: what will change?

Long-term design prepares for the **right** changes, not all changes.

## When to activate
Before choosing a design or abstraction, and when `council-protocol` needs inputs. Run `horizon-fit` first; class A/B with no escalator: skip.

## Standard vectors
Business requirements · Scale (users, data volume) · Data (format, quality, ownership) · Libraries/platforms · External partners and APIs · Law and regulation · Team (new people, departures, knowledge) · Devices and environments · Cost and pricing.

## Procedure
1. For each vector, estimate **P(change within the horizon)**: horizon = 1 year for class C, 5 years for class D (see `horizon-fit`). Use LOW (<20%), MEDIUM (20-60%), HIGH (>60%), and cite the basis (history from `git log`, roadmap, vendor announcements, regulation calendar, past incidents). No basis, no rating: mark UNKNOWN.
2. Estimate the **cost if the change arrives unprepared** (`C_late`) in days or in a coarse band (hours / days / weeks / rewrite).
3. **Rank by expected cost** = P x C_late. Compare the top vectors with the cost of preparing, using the investment rule in `council-protocol`. Prepare only where it clearly pays; otherwise record the vector and a tripwire.
4. Pass the top 2-3 vectors to `change-injection` as test scenarios (code) or to `scenario-stress-test` (finance, when available).
5. Re-rank when facts change; vectors drift.

## Mandatory questions
- Which change has already happened twice in this codebase or domain? (history is the best predictor)
- Which vector is rated LOW only because nobody has looked?

## Output
| Vector | P (basis) | Cost if unprepared | Prepared today? | Conclusion (prepare / tripwire / ignore) |

## Limits
Probabilities are subjective estimates: state the basis for each. UNKNOWN is an honest answer and should lead to a cheap tripwire, not a guess.
