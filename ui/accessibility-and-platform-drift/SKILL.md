---
name: accessibility-and-platform-drift
description: Review a UI for accessibility (keyboard, focus, semantics, contrast, motion, text scaling) and for drift against moving platform targets (browser, OS, framework, design-guideline and legal-standard changes), turning each risk into a checkable test or tripwire. Use when building or reviewing interfaces meant to last, ship to the public, or run on several platforms.
metadata:
  domain: ui
  status: READY
---
# Accessibility and Platform Drift: it must keep working for everyone, on tomorrow's platform

Two long-term failures: the interface excludes users (often by omission), and the interface breaks when the browser, OS or framework moves. Both are cheap to prevent early and expensive to retrofit.

## When to activate
Any interface used by the public or by staff over a long period; before a launch or redesign. Run `horizon-fit` first. Class A/B: still do step 2 for anything handling money, health or legal consequences.

## Procedure
1. **State the standard and the platforms.** Default target: WCAG 2.2 level AA (or the legal standard the product is subject to; check the jurisdiction, because requirements differ and change). List browsers, OS versions, devices and assistive technologies actually supported.
2. **Review the failure-prone areas** and give each a pass, fail or unverified with evidence (`file:line` or a screen):
   - **Keyboard:** every action reachable and operable by keyboard, logical order, no keyboard traps, visible focus indicator that is not removed by `outline: none` without a replacement.
   - **Semantics:** native elements for native behaviour (button, link, input, label); headings in order; landmarks; accessible names for icon buttons and form fields; ARIA only where native HTML cannot do it, and then complete (role, state, keyboard).
   - **Contrast and color:** text and meaningful UI against background meets the ratios of the standard (4.5:1 normal text, 3:1 large text and UI parts for AA); meaning never carried by color alone.
   - **Zoom and text scaling:** usable at 200% text size and 400% zoom without loss of content or horizontal scrolling; relative units; touch targets large enough (at least 24x24 CSS px for WCAG 2.2 AA, larger is better on touch).
   - **Motion and timing:** respects `prefers-reduced-motion`; no content flashing; session timeouts and auto-dismissing messages give enough time.
   - **Forms and errors:** every field labelled; errors identified in text, associated with the field, and announced; no information lost on error.
   - **Dynamic content:** route changes, toasts and loading states announced to assistive technology; focus managed after modals open and close.
3. **Verify, do not assert.** Run an automated checker (axe, Lighthouse or equivalent) and then test by hand: tab through the main flows, zoom to 200%, use a screen reader for one critical flow. Automated tools find only part of the issues, so report which checks were automated and which were manual; anything not run is `unverified`.
4. **Inventory platform dependencies** that can drift: browser APIs and CSS features used (and their support), OS-specific behaviour, framework and library major versions, vendor design-guideline changes, third-party embeds, fonts, payment or identity SDKs, and legal or store-policy requirements. For each, record the version or support assumption in `assumption-ledger`.
5. **Add tripwires** (`assumption-tripwires`): the accessibility check in CI (fails the build on new violations), a browser-support matrix test, a scheduled check of dependency end-of-life dates (`dependency-risk`), and a review date for the standard version.
6. **Prefer standards over workarounds.** A feature built on a platform-specific hack is M11 (extended present); use progressive enhancement with a working baseline so unsupported platforms degrade rather than break.
7. Rank findings by who is blocked and how badly (cannot complete a core flow: HIGH), then fix cost. Log what remains in `debt-ledger` with an owner and date.

## Mandatory questions
- Can a keyboard-only user complete the core flow?
- What happens to the layout at 200% text size?
- Which platform feature are we depending on without a fallback?

## Output
The checklist with pass, fail or unverified per area and its evidence, the dependency and support inventory, the tripwires added, and the ranked remediation list.

## Limits
This is an engineering review, not a certified accessibility audit or legal advice: conformance claims need testing with real assistive technology and, where required, specialist or legal review. Standards and platform support change; confirm current versions before relying on a number here.
