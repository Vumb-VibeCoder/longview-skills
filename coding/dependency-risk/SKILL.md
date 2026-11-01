---
name: dependency-risk
description: Rate the long-term risk of third-party libraries and vendor services: abandonment, deprecation, unpinned versions, missing lockfiles, license or ownership changes, and how costly each would be to replace. Use when adding, upgrading or removing a dependency, reviewing package.json / requirements / pyproject, or before building on a vendor API in long-lived (class C/D) software. Ships an offline manifest scanner.
metadata:
  domain: coding
  status: READY
---
# Dependency Risk: what will this cost when it goes wrong?

Risk = **how likely the dependency is to cause trouble** x **how expensive it is to leave**. Both must be evidenced.

## When to activate
Adding, upgrading, replacing or auditing dependencies; choosing a vendor service. Run `horizon-fit` first. Class A/B with no escalator: only check that versions are pinned, then stop.

## Required inputs
The manifests (and lockfiles) and whether the project is an **application** (deploys itself) or a **library** (others install it). The policy differs: an application needs exact versions fixed, either by a committed lockfile or by exact pins in the manifest (ranges in the manifest are then fine); a library needs compatible ranges tested at both bounds, and its ranges are never a defect.

## Procedure
1. **Inventory (measured):** `python scripts/dep_scan.py <project_dir>`. It reports pin status (PINNED, COMPATIBLE_RANGE, RANGE, UNPINNED, SOURCE_URL) and manifests without a lockfile.
2. **Hygiene findings** (apply the policy for app vs library). Application: no lockfile AND no exact pins; or a SOURCE_URL dependency (git URL/branch/local path) not pinned to a commit or tag. UNPINNED or RANGE entries are findings only when no lockfile exists. Library: UNPINNED (no constraint at all) or SOURCE_URL runtime dependencies.
3. **Exposure (measured):** for each load-bearing dependency count the files that import it (`grep -rIl "<import name>" <src> | wc -l`). Classify the replacement surface:
   - **Contained:** <= 3 files, or behind one module
   - **Spread:** 4-20 files
   - **Pervasive:** > 20 files, or its types appear in your public interfaces or stored data
4. **Health (evidenced from upstream):** for each Spread/Pervasive dependency and every one on a critical path, gather from the registry/repository and **cite the source and date**: last release, last commit, archived/deprecated notice, maintainer count, response to critical issues, license changes, known security advisories (run `pip-audit` / `npm audit` if available). Anything you could not verify is labelled **UNVERIFIED**; do not infer health from memory. Rate:
   - **AT-RISK:** archived/deprecated, or an unfixed critical advisory, or no release for 24+ months while the domain keeps moving (protocols, security, platform APIs), or a maintainer announcing departure
   - **WATCH:** 12-24 months without a release in a moving domain, single maintainer, 2+ major versions behind, license or ownership change
   - **HEALTHY:** none of the above. A small, stable, finished library with no open critical issues is HEALTHY despite its age.
5. **Decide per dependency:**

   | Health \ Exposure | Contained | Spread | Pervasive |
   |---|---|---|---|
   | AT-RISK | replace at next touch | plan migration; add a seam | **MUST ACT**: migration plan + seam + owner |
   | WATCH | accept + tripwire | accept + tripwire | add a seam now, tripwire |
   | HEALTHY | accept | accept | accept; record as assumption |
   | UNVERIFIED | verify before deciding | verify before deciding | verify before deciding |

6. **Seam rule:** add a thin wrapper only when health is AT-RISK/WATCH, or lock-in is real, **and** exposure is Spread/Pervasive. A wrapper around a HEALTHY or Contained dependency is M10.
7. **Tripwires:** for each WATCH/AT-RISK dependency record the assumption "X stays maintained" in `assumption-ledger` and attach a check via `assumption-tripwires` (for example: no release for 12 months, or an advisory without a fix).
8. Score with `verdict-format` (mainly Reversibility, Assumption fragility, Cost of failure).

## Mandatory questions
- If the maintainer disappears tomorrow, what is the first thing that breaks and how many files change?
- Does the dependency's data format or types leak into our storage or public API?
- Is there a standard-library or 20-line alternative for what we actually use?

## Output
```
| Dependency | Pin status | Exposure (files) | Health + source/date | Decision | Tripwire |
Hygiene findings: ...
MUST ACT items: ...
UNVERIFIED items and how to verify them: ...
```

## Exit path
- **Missing input:** no manifest or lockfile: say so and list what to provide; do not rate from memory.
- **Script problem:** if `dep_scan.py` exits 2 or crashes, fix the input once and retry. If it still fails, write `NOT MEASURED: <script>`, give a bound you can compute by hand, and do not quote a number.
- **Stop or hand off:** a vendor that cannot be checked offline gets `UNVERIFIED`, not a guessed score.

## Limits
Offline scan sees only declared direct dependencies; transitive risk needs the ecosystem audit tool. Health depends on external facts that change: every health rating carries a date and expires with its tripwire. Monorepo path-based dependencies are reported as SOURCE_URL and must be judged by hand.
