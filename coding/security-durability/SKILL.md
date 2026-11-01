---
name: security-durability
description: Review code or a design for security mistakes that are expensive to fix later - exposed secrets, missing key rotation, untrusted input, over-wide permissions, unsafe deserialization, weak crypto choices, personal data kept without a reason. Use for anything touching auth, payments, personal data, file uploads, public endpoints or credentials, and before publishing a repo. Ships a pattern scanner and a threat model template.
metadata:
  domain: coding
  status: READY
---
# Security Durability: find what is cheap to fix now and costly later

Security flaws get more expensive the longer they live: a leaked key is in git history forever, and a missing permission model is hard to retrofit. This skill finds the known-bad patterns with a script and asks the design questions that a script cannot.

## When to activate
Class C/D work (`horizon-fit`), and any class where money, personal data, credentials, file uploads or a public endpoint is involved. Also before making a repository public. For a throwaway local script, run only the secret check.

## Required inputs
The code or design, who can reach it (just you, your team, the internet), what it stores or can change, and which secrets it uses. If you cannot say who can reach it, ask.

## Procedure
1. **Run the scanner** on the code: `python scripts/scan_security.py PATH`. Read every high finding yourself and mark it real or false positive with a reason.
2. **Secrets first.** Any real secret in code or history counts as leaked: rotate it, then remove it. Deleting the line is not enough. Move secrets to environment or a secret store, and name who rotates them and how often.
3. **Draw the trust boundary.** List where input enters (forms, APIs, files, webhooks, environment, other services) and treat all of it as untrusted until validated. Use `templates/threat-model.example.md`.
4. **Check the four standard failures at each entry point:** input is validated and size-limited; the caller is identified and allowed (authentication and authorisation checked on the server, not just in the UI); output is escaped for where it goes (HTML, SQL, shell, logs); errors do not reveal internals.
5. **Least privilege.** Each token, database user and service account gets only what it needs. Note anything with admin rights and why.
6. **Data you keep.** For every piece of personal or sensitive data: why it is kept, who can read it, how long, and how it is deleted. If there is no reason, do not store it.
7. **Dependencies and updates.** Hand the third-party risk to `dependency-risk`. Say how security fixes reach production (who notices, how fast).
8. **Write down what stays open.** Each accepted risk goes into `debt-ledger` with an owner and a re-check date, or into an `assumption-tripwires` entry if it depends on an assumption such as "only staff can reach this".
9. **Add a guard.** Turn the findings that can be automated into `fitness-functions` rules (for example "no `verify=False`") so they do not come back.

## Mandatory questions
- If this key or password leaked today, what would an attacker reach, and how fast could we rotate it?
- What is the worst thing a malicious but logged-in user could do?
- Which input reaches a database, a shell, a file path or a template without validation?
- What personal data do we hold that we could not explain to its owner?
- How would we notice a break-in?

## Output
Findings ranked by severity, each with `file:line` or the design element, why it matters, and the fix. Then the open risks with owners. Use `verdict-format` for a class C/D verdict, with the scanner output as evidence. A review with no code or design to look at is `INSUFFICIENT EVIDENCE`, never a guessed list.

## Exit path
- **Missing input:** no code or design supplied, or you do not know who can reach it: ask. Do not list generic risks as if they were findings.
- **Script problem:** if `scan_security.py` exits 2 or crashes, fix the path once and retry. If it still fails, write `NOT MEASURED: scan_security.py`, review by hand, and say the pattern check was not run.
- **Stop or hand off:** a real leaked secret stops everything else: rotate first, then continue. For incidents already in progress (active breach, data exposed), give containment steps and recommend a qualified security professional; this skill does not replace one. Credentials in published history also go to `rollback-path` for the cleanup plan.

## Limits
The scanner matches known patterns line by line. It misses logic flaws (broken access control, race conditions, business-rule abuse), flags some safe code, and does not read compiled or minified files. It is not a penetration test, a compliance audit or legal advice. A clean scan means "no known-bad pattern found", not "secure".
