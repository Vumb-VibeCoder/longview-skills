---
name: module-boundary-review
description: Evidence-based review of module/package/service boundaries using measured coupling (fan-in, fan-out, instability, import cycles) plus git co-change history. Use when deciding where code should live, before adding a cross-module dependency, when a change keeps touching several modules, or when judging a split or merge of modules in a long-lived (class C/D) codebase. Ships scripts that measure the graph.
metadata:
  domain: coding
  status: READY
---
# Module Boundary Review: are the seams in the right place?

A boundary is justified by how things **change**, not by how they look. This skill measures first, then reads.

## When to activate
Class C/D code (run `horizon-fit` first; class A/B with no escalator: stop). Typical triggers: a feature touches 3+ modules, a new cross-module import is proposed, a package is being split or merged, "where should this live?".

## Required inputs
Source root, the language(s), and (strongly preferred) a git history. If there is no git history, skip step 3 and say co-change is unmeasured.

## Procedure
1. **Measure the graph:** `python scripts/module_graph.py <src> --depth 1` (then `--depth 2` for the busiest module). Record fan-in, fan-out, instability `I = out/(in+out)`, and cycles. Static imports only.
2. **Cycles first:** every import cycle between modules means they cannot be changed, tested or deployed separately. Each cycle is a finding (M07) unless the "modules" are deliberately one unit.
3. **Measure hidden coupling:** `python scripts/cochange.py <repo> --src <src_dir>`. A pair with strength >= 0.6 and >= 5 co-changes that has **no import edge** is hidden coupling (shared data shape, DB table, config key, duplicated logic M04, protocol). Find the shared thing and name it.
4. **Read the evidence, do not trust the numbers:** for each cycle edge, each high-strength pair and each edge where a more stable module depends on a more volatile one (heuristic: `I(target) - I(source) >= 0.3`; a prompt to look, not a defect), open the importing line and classify it:
   - uses the target's **public interface** (acceptable)
   - **reaches into internals** (M07)
   - shares a **data structure/table/schema** (name the owner)
   - **calls back** to create a cycle
5. **Justify every boundary.** A boundary is justified only if at least one holds: different rate of change, different owner/team, different deployment or scaling, a stable contract with >= 2 consumers, security/compliance isolation. A boundary meeting none of these, with high co-change strength, is a **merge candidate** (M10 over-split).
6. **Propose the smallest cuts:** invert a dependency, move one function/type, introduce an interface at a seam **that already has two sides**, or merge two modules. Prefer moving 1 thing over creating 1 layer.
7. Feed the evidence into `verdict-format`; this skill mainly drives **Coupling** and **Change tolerance**. Use `council-protocol` for any merge/split proposal and record the accepted one with `adr-writer`.

## Mandatory questions
- If the most plausible requirement change arrives, which modules must be edited? (cross-check with `change-injection` when available)
- Which module is the real owner of each shared data structure?
- Which boundary here would nobody miss if it were deleted?

## Output
```
Graph: <files> files, <modules> modules, <edges> edges, <cycles> cycles
| Finding | Evidence (file:line / metric) | Pattern | Level (MUST/SHOULD/ACCEPTABLE) | Smallest fix |
Boundaries to cut/invert: ...
Boundaries to merge (unjustified): ...
Boundaries worth adding: only with a stated justification from step 5
Coupling & Change tolerance scores with evidence (verdict-format)
```

## Limits
Sees static imports only. Coupling through databases, queues, HTTP, reflection, dynamic imports, build config or tests is invisible to the graph (the co-change step is the partial remedy). Test directories are skipped by default. JS/TS import resolution is approximate (relative imports only). Co-change reflects past habits and shrinks right after a reorganisation.
