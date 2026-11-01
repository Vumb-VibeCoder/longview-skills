---
name: skill-name
description: One or two sentences, under 1024 characters: what it does AND when to use it (the trigger words a user would say). Mention bundled scripts.
metadata:
  domain: core | coding | finance | design | ui
  status: PLANNED | READY
---
# Skill Name: one-line purpose

Why this skill exists, in two sentences.

## When to activate
Concrete signals. State which `horizon-fit` classes it applies to.

## Required inputs
What to read or ask first. If missing: ask or stop; never guess silently.

## Procedure
1. Numbered, ordered, each step checkable. Reference other skills by name in backticks.
2. Include decision rules with an explicit order ("first match wins") and no overlapping conditions.

## Mandatory questions
- Questions the AI must answer with evidence before concluding.

## Output
The exact shape of the result. Use `verdict-format` when a verdict is needed.

## Limits
What this skill cannot conclude; known false-positive sources; what was not measured.
