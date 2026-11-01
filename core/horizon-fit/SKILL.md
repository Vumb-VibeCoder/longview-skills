---
name: horizon-fit
description: Decide how long a thing must live (class A-D) and therefore how much long-term design it deserves. Run FIRST, before writing, changing, designing or reviewing anything that will outlive the current conversation (code, systems, financial models, UI), to prevent both short-sighted work and over-engineering.
metadata:
  domain: core
  status: READY
---
# Horizon Fit: how long must this live?

Always runs first. It guards against BOTH failure modes: short-sightedness (treating a lasting thing as disposable) and over-engineering (building a platform for a throwaway script).

## When to activate
Any request to write, change, design or evaluate something that will exist after this conversation ends.

## Required inputs (ask, or infer WITH cited evidence; never guess silently)
1. **Expected lifetime (L):** once / up to 3 months / more than 3 months / years.
2. **Dependents (N):** how many people, systems or external consumers rely on it or on its interface.
3. **Failure cost (F):** what a failure destroys: only time / data / money / security / legal or safety.
4. **Churn:** how fast the domain moves (requirements, libraries, regulation).

## Procedure
1. Evaluate every rule below. **The highest class triggered wins.**

   | Class | Name | Triggered when |
   |---|---|---|
   | A | One-off | L = once AND N = 0 AND F = time only |
   | B | Prototype | L <= 3 months AND N <= 1 (author or own team) AND F = time only |
   | C | Living product | L > 3 months, OR any real user/dependent exists, OR the escalators below fire |
   | D | Platform | L = years AND (N >= 3 dependents, OR it exposes a public/external interface or library API) |

2. **Escalators** (apply per component, not only to the whole):
   - F includes data, money, security, legal or safety, so the components touching that risk are **at least class C**, even inside a class A/B project.
   - A class B thing older than 6 months is reclassified **C**.
   - Real users exist, so **at least C**.
3. If the result is **A or B** (and no escalator fired): verdict is TEMPORARY IS ENOUGH. Do only these: (a) make it correct, (b) record its debt with `debt-ledger`, (c) record the re-class trigger below. A secret (webhook URL, token, key) still goes in an environment variable, even in class B: it is one line and the cost of a leak does not shrink with the project. Stop; do not run council or three-horizon work.
4. If a **mixed** result (e.g. a B prototype with one C component): split it. Apply the C/D process only to the escalated components and say which. Print the project class first and each escalated component with its own class: `CLASS: B | Components escalated: SMS sending -> C`. Do not print `C` for the whole project, because that triggers council and three-horizon work on the parts that are a throwaway. The rest of the project follows the TEMPORARY IS ENOUGH path.
   A lifetime with no end date does not make a one-user script class C: own use plus time-only failure cost is class B, and the re-class trigger names what would change it (a second user, a shared repo, a date).
5. If **C or D**: continue the standard flow: `assumption-ledger`, the domain skills, `council-protocol`, `three-horizon-map`, `verdict-format`.
6. If inputs conflict or are missing and cannot be asked: classify on the evidence you have, mark the class **PROVISIONAL**, and name the one input whose answer would change the class.

## Horizon by class (single definition used by every skill)
A/B = its stated lifetime (at most 3 months). C = 1 year. D = 5 years. Probability scale for "within the horizon": LOW < 20%, MEDIUM 20-60%, HIGH > 60% (cite the basis: history, trend, owner statement).

## Mandatory questions
- If this lives 10x longer than planned, what breaks first?
- If it dies sooner than planned, which investment is wasted?
- Prototypes become permanent: what evidence shows that is happening here (users, other code importing it, age, data it now holds)?

## Failure patterns to avoid
| Pattern | Description |
|---|---|
| Short-sighted | Treating everything as class A even though users or money are involved |
| Over-engineered | Class D architecture for a one-off script (see M10 in `myopia-patterns`) |
| Temporary became permanent | Class B for more than 6 months, still handled as B |
| Whole-project averaging | Classing the entire project B and ignoring the one component that holds money or data |
| Reverse averaging | Classing the whole throwaway C because one component holds money, data or personal contacts; only that component is escalated |

## Output (exact shape)
```
CLASS: <A|B|C|D> [PROVISIONAL] | Components escalated: <none | component -> class, ...>
Reason: <2-3 sentences citing the evidence for L, N, F>
Consequence: TEMPORARY IS ENOUGH | continue to standard flow
Re-class trigger: <one concrete observable event that forces re-classing>
```
When the consequence is TEMPORARY IS ENOUGH, the answer continues with exactly this block and nothing heavier:
```
Do: <the correct thing, built as small as it can be>
Safeguard (max one): <what it prevents, with the failure cost it answers | none>
Debt: <what was deliberately left out and its likely interest>
Re-class trigger: <same event as above>
```
A feature that is not required for correctness and does not answer a named failure cost is cut (M10).

## Exit path
- **Missing input:** lifetime and users unknown: give the answer for both readings (for example internal versus published) and name the fact that decides it.
- **Stop or hand off:** if class is A/B with no escalator, follow the TEMPORARY IS ENOUGH path and stop.

## Limits
It cannot predict the future. It sets a reasonable investment level from present information, and must be re-run when that information changes.
