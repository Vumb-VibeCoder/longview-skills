---
name: design-token-discipline
description: Enforce that colors, spacing, type sizes, radii and z-indexes come from a small named token set instead of hard-coded values, and design the token layers so a rebrand, dark mode or density change is a one-file edit. Use when building or reviewing UI styling, theming, or a design system. Ships ui_scan.py, which counts hard-coded values outside token definitions and finds near-duplicate colors.
metadata:
  domain: ui
  status: READY
---
# Design Token Discipline: one decision, one name, one place

Hard-coded values are M01 at UI scale: the brand blue exists in 40 places, so a rebrand is 40 edits and three get missed. Tokens turn visual decisions into data.

## When to activate
Writing or reviewing styles, themes or a component library. Run `horizon-fit` first: class A/B (a prototype, a one-page tool) may use literals; class C/D needs tokens. Escalate if the UI is shared across products or must support themes.

## Procedure
1. **Measure first:** `python scripts/ui_scan.py src/`. It reports, per category (color, font size, spacing, z-index), the number of hard-coded uses outside token definitions, the number of distinct values, the most repeated literals, and near-duplicate colors (within a few RGB steps, usually one intent that drifted). Token definitions (CSS custom properties, SCSS variables, files named tokens/theme/variables) are not counted as violations.
2. **Judge the distinct counts.** Rough health guide: colors under about 15 outside neutrals, font sizes under about 8, spacing steps under about 10, z-index values under about 6. Far above that means there is no scale, only accumulation.
3. **Define three layers, no more:** (a) primitive values (`blue-500: #3366ff`), (b) semantic tokens naming purpose (`color-action`, `color-text-muted`, `space-3`), (c) component tokens only where a component truly varies. Components reference semantic tokens, never primitives. Dark mode and rebrands change layer (b)'s mapping, not component code.
4. **Merge before naming.** Collapse near-duplicates and close sizes into the nearest scale step; record each merge, since it changes pixels. Keep the scale small: spacing on a 4 or 8 base, a modular type scale, z-index as named layers (`dropdown`, `modal`, `toast`) rather than numbers like 9999.
5. **Replace literals by token, most repeated first,** and only literals that express a design decision. Leave true constants alone (0, 1px hairlines, 100%) and one-off values that are intentionally unique and commented.
6. **Prevent regression:** add a lint rule or a CI check that fails on new hex/rgb literals outside the token files (see `fitness-functions`: a rule with a `why`, e.g. "rebrand must be a one-file change"). Re-run `ui_scan.py` and record the before and after counts.
7. **Check the test of the system:** change the primary color token and one spacing token, and confirm the whole UI follows without touching component files. If something does not follow, a literal is hiding.
8. If a token rename or removal affects consumers of the library, treat it as an API change (`component-api-stability`).

## Mandatory questions
- If the brand color changes tomorrow, how many files change?
- Does dark mode or a high-contrast theme require editing components?
- Which two tokens are different names for the same decision?

## Output
Before and after counts per category, the token layers with the merge decisions, the lint or CI rule added, and the result of the one-token-change test. For a verdict use `verdict-format` (Change tolerance carries the most weight).

## Limits
The scanner is regex-based: it does not resolve CSS-in-JS built dynamically, values inside images or SVG files, or runtime-computed styles; it may count literals in generated code. Counts guide judgment; they are not a pass/fail standard by themselves.
