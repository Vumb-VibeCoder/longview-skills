---
name: failure-and-scale-modes
description: Enumerate how a system fails and where it saturates - dependency outages, partial failure, overload, retries, data growth, hot keys, backpressure, recovery and detection - and check each has a defined behaviour, a limit and a signal. Use when designing or reviewing services, queues, databases, integrations or anything that must run unattended or at growing load.
metadata:
  domain: design
  status: READY
---
# Failure and Scale Modes: know how it breaks before it does

Systems rarely fail where the diagram says. They fail at the edges: a slow dependency, a retry storm, a table that outgrew its index, a queue nobody watches. This skill forces each failure to have a defined behaviour.

## When to activate
Any system with dependencies, shared state or growth. Run `horizon-fit` first; class A/B needs only steps 1 and 7. For F = money, data or safety, run all steps.

## Procedure
1. **List the components and their dependencies** (databases, third-party APIs, queues, caches, disks, clocks, humans). For each dependency write what the system does when it is: down, slow, returning errors, returning wrong data.
2. **Fill the failure table.** For every dependency and every failure mode, state: the behaviour (fail fast, degrade, queue, retry, serve stale), the user-visible effect, the data-integrity effect, and the signal that tells an operator (metric, alert, log). A cell that says "unknown" or "it will probably error" is a finding.
3. **Check the amplifiers.** Retries without backoff, jitter and a cap; timeouts missing or longer than the caller's; unbounded queues; synchronous chains of 3+ services; shared connection pools; one slow dependency blocking unrelated work. Each amplifier turns a small failure into an outage.
4. **Check partial failure and idempotency.** For each operation that changes state across two systems, say what happens if it stops halfway, and whether it can be safely repeated. Operations touching money or inventory must be idempotent or reconciled. If neither, do not output KEEP (REINFORCE at best, per `verdict-format`).
5. **Find the saturation points.** For each resource (CPU, memory, connections, disk, rows, queue depth, rate limits) estimate current use, the growth rate and the time to the limit using the stated load assumptions. Report in time ("full in ~14 months at 8%/month"), not in raw numbers. Any limit reached within the horizon needs a plan or a tripwire.
6. **Look for non-linear growth:** operations that grow with the square of data, unbounded lists in a single record, full scans on a growing table, hot keys, fan-out per event. These look fine in testing and fail at 10x.
7. **Check recovery:** can the system restart cleanly, is there a backup, has a restore been tried (an untested backup is not a backup), what is the time to recover and the data lost, and is the runbook current? Also check the human mode: what if the one person who understands it is away?
8. **Record the load and growth assumptions** in `assumption-ledger` and give each saturation point a tripwire (`assumption-tripwires`), e.g. "alert at 60% of disk or 12 months to limit".
9. **Prove one failure:** pick the most likely or most damaging failure and test it in a safe environment (kill the dependency, fill the queue, restore the backup). A failure mode that has not been exercised is only a hypothesis; mark which rows are tested.
10. Finish with `verdict-format` (Operability and Cost of failure carry the most weight).

## Mandatory questions
- What happens to users and data when each dependency is down for an hour?
- Which resource fills up first, and when?
- Who finds out, how, and how fast?

## Output
The failure table, the amplifier findings, the idempotency findings, the saturation table with time-to-limit, the recovery check with what was actually tested, the tripwires, and the verdict.

## Exit path
- **Missing input:** no load or dependency numbers: ask, or give the failure modes without capacity claims.
- **Stop or hand off:** with no architecture description, stop and list what is needed.

## Limits
Estimates come from stated assumptions, not measurements; label them. This review does not replace load testing, chaos testing or a security review. Distributed-system faults can interact in ways a table does not predict.
