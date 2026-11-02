---
name: api-contract-stability
description: Judge whether a change to an interface other people's code depends on will break them - HTTP and RPC APIs, library public functions, CLI flags, config files, file formats, event and message schemas, and database schemas read by other services. Classifies each change as BREAKING, RISKY or SAFE by direction (request versus response), checks for a migration path and deprecation window, and covers meaning that no schema diff can see. Use when changing, versioning or releasing an API, "will this break clients", "is this backward compatible". Ships contract_diff.py, which compares two OpenAPI 3 or JSON Schema files.
metadata:
  domain: coding
  status: READY
---
# API Contract Stability: who breaks if this ships?

An interface is a promise to code you do not control. This skill finds the promises a change breaks, who they break for, and the safe way to make the change anyway. For UI component props use `component-api-stability`; this skill covers everything else that has outside consumers.

## When to activate
Changing, versioning or releasing anything with consumers outside the change: a public or partner HTTP API, a library's exported functions, CLI flags and exit codes, config or file formats, message and event schemas, a database schema another service reads. Run `horizon-fit` first. Class C/D when consumers are external or deploy on their own schedule. If the only consumer is deployed together with the provider in one release, the risk is low (class A/B): say so, check that the two really ship together, and stop.

## Required inputs
1. The old and the new contract: OpenAPI 3 or JSON Schema as JSON for the script; for other forms (protobuf, function signatures, CLI help text, a table definition) the two versions as text.
2. Who consumes it and how they upgrade: internal services, partners, public clients, mobile apps that cannot be force-updated.
3. Whether the change is already released. If missing, ask; the answer changes the plan from "avoid" to "migrate".

## Procedure
1. **List the contract surface** the change touches: endpoints, fields, parameters, status and error codes, flags, file layouts, message names, table columns.
2. **Measure:** `python scripts/contract_diff.py OLD.json NEW.json`. OpenAPI documents are judged by direction automatically; for a bare JSON Schema pass `--mode request`, `--mode response` or leave the default `both`. It prints BREAKING, RISKY and SAFE changes with locations and exits 1 if anything is BREAKING. For formats the script cannot read, do the same classification by hand with the direction rules below and say the script was not run.
3. **Apply the direction rules.** In what clients send (requests, config files, inputs), tightening breaks them: a new required field, a removed enum value, a lower maximum, a new auth requirement. In what clients read (responses, events, output files), removing or retyping breaks them: a removed field, a type change, a field no longer guaranteed, a response that can now be null. Added enum values in a response are RISKY, because clients with an exhaustive switch can fail.
4. **Check meaning, which no diff sees.** Units, rounding, default values, ordering, pagination, idempotency, rate limits, error codes and retry behaviour are part of the contract. For each, ask whether any consumer could be relying on the old behaviour. Assume someone does: any observable behaviour gets depended on.
5. **For every BREAKING or RISKY change, choose a path** in this order:
   1. Do not make the change (add a new field or endpoint beside the old one).
   2. Make it additive, then remove later in a separate, announced step (expand, migrate consumers, contract).
   3. Version it (new path, header or package version) and keep the old one running for a stated period.
   4. Break it deliberately: only with the consumer list notified, a dated deprecation, a kill switch and a rollback per `rollback-path`.
6. **Find the real consumers.** Use access logs, usage metrics or a code search across known callers, not the documentation. Name who was checked and who was not.
7. **Record and enforce.** Write the decision with `adr-writer`; add the script to CI against the last released contract with `fitness-functions`, so a breaking change cannot ship by accident.

## Mandatory questions
- Who calls this today, and how do you know (logs, metrics, code search)?
- Can every consumer upgrade at the same moment the provider does? If not, which versions must run side by side?
- What is the way back if a consumer breaks after release, and who pulls the trigger?
- Which meaning (unit, default, order, error code) changed without the schema changing?

## Output
| Change | Class | Who breaks | Safe path | Decision |
One row per BREAKING or RISKY change, from the script output plus any meaning changes found by hand. Then: SAFE count, consumers checked and not checked, and the chosen migration or deprecation plan with dates. Use `verdict-format` only if a scored verdict is requested. See `templates/contract.old.example.json` and `templates/contract.new.example.json` for an example pair.

## Exit path
- **Missing input:** only one version of the contract, or none: ask for both; do not guess what changed. Unknown consumers: report the change as BREAKING until consumers are known.
- **Script problem:** exit 2 means an unreadable file, YAML instead of JSON, a Swagger 2 document or a bad option: convert once and retry. If it still fails, write `NOT MEASURED: contract_diff.py` and classify by hand using the direction rules.
- **Stop or hand off:** one-way changes go to `reversibility-check` and `rollback-path`. Choosing a database or protocol from scratch is `system-design-longevity`.

## Limits
The script reads JSON only, resolves local references only, follows the OpenAPI 3 structure and compares composition keywords (oneOf, anyOf) by position. It sees structure, not meaning, ordering or performance, and it cannot know who the consumers are. A clean result means no structural break was detected, not that the change is safe. Swagger 2, GraphQL, protobuf and YAML must be converted or checked by hand.
