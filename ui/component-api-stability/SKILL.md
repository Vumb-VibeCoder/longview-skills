---
name: component-api-stability
description: Keep a UI component's props, events, slots and CSS hooks stable for consumers - classify each API change as breaking or safe, add deprecation paths instead of removals, and keep the surface small. Use when changing a shared component or design-system library, reviewing a component's props, or releasing a UI package. Ships props_diff.py, which compares TypeScript props between two versions and exits 1 on breaking changes.
metadata:
  domain: ui
  status: READY
---
# Component API Stability: consumers should not be surprised

A component's public surface (props, events, slots, class names, data attributes, exported names, behaviour defaults) is a contract. Every consumer who depends on it is a dependent N in `horizon-fit` terms; changing it is a one-way door unless handled deliberately.

## When to activate
Changing a component used by more than one caller, adding props, renaming, or releasing a shared library. For a component with one caller in the same repo, simply update both and stop.

## Procedure
1. **Define the public surface** explicitly: what is documented or exported is public; everything else is private. Anything consumers can reach (class names, DOM structure, `data-` attributes, default values, event order) is effectively public if consumers use it. List what you know is used (search consumers, `grep` for usage).
2. **Diff the props:** `python scripts/props_diff.py old.tsx new.tsx [PropsTypeName]`. It classifies each change. Breaking: REMOVED, ADDED_REQUIRED, OPTIONAL_TO_REQUIRED, TYPE_CHANGED. Safe: ADDED_OPTIONAL, REQUIRED_TO_OPTIONAL. Exit code 1 means a breaking change exists. Review its TYPE_CHANGED lines by hand: widening an input type is safe, widening a callback parameter or return type is not.
3. **Check what the script cannot see:** changed default values, changed event timing or payload, changed DOM structure or class names, changed accessibility behaviour, changed side effects, changed peer dependencies. Each of these is breaking if a consumer can observe it.
4. **Choose the path for every breaking change:**
   - Add the new prop alongside the old one, keep both working, mark the old `@deprecated` with the replacement and a removal version or date, emit a dev-time warning. Remove only in a major release.
   - If the change is a bug fix that consumers could depend on, decide explicitly (and record it) whether the old behaviour is preserved behind an option.
   - If there is truly no compatible path, it is a major version with a migration note and, for many consumers, a codemod.
5. **Keep the surface small.** Prefer composition (slots, children) over a new boolean prop for every variant. More than about 3 boolean props that interact, or props whose combinations are invalid, signal M08 (do-everything component): replace with a variant prop or separate components. Every new prop is a permanent obligation (M10 if no second use exists).
6. **Make required props required for a reason.** Defaults should be safe and accessible. A default change is breaking.
7. **Version honestly:** removal or breaking change means a major bump; additive means minor; fixes mean patch. Run the props diff in CI so a breaking change cannot ship under a minor version (`fitness-functions`).
8. Record deprecations with a deadline and owner in `debt-ledger` or `assumption-tripwires`; "deprecated forever" is a leak.

## Mandatory questions
- Who uses this prop, and how do we know?
- Can old and new callers work at the same time?
- Which observable behaviour changed that the type diff cannot show?

## Output
The prop diff, the manual-check list, each breaking change with its compatibility path and version impact, and the CI check added.

## Exit path
- **Missing input:** no old and new API to compare: ask for both versions.
- **Script problem:** if `props_diff.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** if consumers are unknown, treat every public prop as breaking.

## Limits
`props_diff.py` is regex-based: it reads `interface X {}` or `type X = {}` blocks with simple members, and may miss props from `extends`, intersections, generics or imported types. Treat a clean result on a complex type as unverified. It does not cover Vue, Svelte or non-TypeScript components.
