---
name: consistency-audit
description: Audit a UI for inconsistency - the same intent expressed in different values, components, states, copy or interaction patterns - ranking findings by user impact and by cost to fix. Use before a redesign, when onboarding a design system, or when a product feels patched together. Ships ui_scan.py to count distinct values and near-duplicates as objective evidence.
metadata:
  domain: ui
  status: READY
---
# Consistency Audit: same intent, same expression

Inconsistency is how a UI decays: each screen is locally reasonable and the whole is not. The audit finds where one intent has several forms, then decides which form wins.

## When to activate
A product with several screens, authors or years of history; before adopting or extending a design system; after a merge of two products. Run `horizon-fit` first (class A/B: skip).

## Procedure
1. **Collect objective evidence:** `python scripts/ui_scan.py src/` gives distinct colors, font sizes, spacing values and z-indexes, with near-duplicates. Many distinct values for one purpose is the numeric signature of drift.
2. **Build an inventory of repeated intents** by walking the real screens (or screenshots; say which): buttons (primary, secondary, destructive), inputs, links, modals, tables, empty states, loading states, error messages, confirmations, dates and numbers, icons. For each intent, list the distinct forms found with the file or screen where each lives.
3. **Check each intent across five axes:** appearance (size, color, radius), behaviour (hover, focus, disabled, loading, keyboard), copy (terms, capitalization, tone: "Delete" vs "Remove"), layout (spacing, alignment, order of primary/secondary actions), and states (is every state designed, or only the happy one?).
4. **Classify each inconsistency:**
   - HARMFUL: users can make mistakes or lose time (destructive action styled like a normal one, two meanings for one icon, different keyboard behaviour for the same control).
   - VISIBLE: looks careless but does not mislead.
   - INVISIBLE: differs in code or tokens but not on screen.
5. **For each, decide the winner by evidence:** the form used most, the form that meets accessibility (`accessibility-and-platform-drift`), or the one the user flows depend on. Never pick by taste alone, and do not average two forms into a third.
6. **Prioritise** by user impact first, then spread (how many places), then fix cost. Fix HARMFUL items first; batch VISIBLE items into the token and component work (`design-token-discipline`, `component-api-stability`); leave INVISIBLE items unless they hinder change.
7. **Write the rule, not just the fix:** for each decided intent add it to the design system or a short style guide with one example, so the drift does not return.
8. Re-run the scanner and compare distinct counts; log remaining items in `debt-ledger` with an owner.

## Mandatory questions
- Which inconsistency could make a user do the wrong thing?
- Is any state (error, empty, loading, disabled) missing for a common component?
- Which form do the accessible implementations use?

## Output
The inventory table (intent, forms found, winner, class, fix cost), the scanner before and after, the prioritised list, and the rules added to the style guide.

## Limits
Only screens and files actually examined are covered; state which. Taste differences are not findings: every finding needs two concrete locations that show the divergence. The scanner sees code, not rendered pixels.
