# BullSignal — engineering case study

This document is a public-safe description of engineering work around BullSignal. It intentionally excludes production credentials, private datasets, trading rules, hostnames, IP addresses, provider names, deployment paths, account identifiers and live infrastructure details.

The public version describes engineering decisions, not the production topology.

## Problem

BullSignal grew from a website into a system with several moving parts: web backend, Telegram UX, external APIs, background jobs, analytics experiments, monitoring and deployment tooling.

The hard part was not adding one more feature. The hard part was changing one component without silently breaking another one.

## What I worked on

### Telegram and backend integration

- command and callback routing;
- API-backed user actions;
- duplicate-delivery protection;
- separation of profile, trading, security and monitoring flows;
- confirmation gates for actions with side effects.

### Reliability

- health checks and incident states;
- fail-closed behaviour when required state is missing;
- retry/verification logic where it is safe;
- explicit rollback paths for deploys;
- separating mutable runtime state from source code.

### Deployment

The deployment flow was designed around small reviewable changes rather than ad-hoc editing of deployed files.

Typical sequence:

1. inspect the intended change;
2. verify the expected baseline;
3. create a recoverable checkpoint;
4. apply the smallest required change;
5. run checks;
6. keep a tested rollback path.

The public portfolio intentionally does not document the real hosts, providers, service paths, deployment endpoints or operator accounts used by the project.

### Analytics research

Research code is isolated from production and real trading. Experiments use deterministic inputs where possible, keep out-of-sample periods sealed until the right stage, and record enough evidence to reproduce a decision.

## Example engineering problems

### Duplicate Telegram actions

A callback can be delivered or handled more than once. Treating each handler call as unique is unsafe when it can create a second message or repeat a state change.

The useful lesson was to think in terms of **idempotency** instead of trying to patch individual duplicate symptoms.

### Stale market data

A UI can look healthy while its underlying cache is stale. A reliable design needs an explicit freshness contract, not just a successful HTTP response.

That led to separating:

- data availability;
- data freshness;
- API health;
- frontend rendering state.

### Deployed state vs repository state

A repository snapshot can drift away from what is actually deployed. The safer approach is to verify the deployed state and the relevant change history before making another production change instead of assuming an old checkout is current.

The exact production layout is intentionally omitted from the public case study.

## What I learned

- integrations fail at boundaries more often than inside a single function;
- rollback is part of a feature, not an emergency afterthought;
- automation should stop on ambiguous state instead of guessing;
- logs need to answer "what happened?" and "what changed?";
- a working prototype and a maintainable system are different stages of a project.

## Stack touched

PHP, Python, SQL, REST/HTTP, Telegram Bot API, Linux, GitHub Actions, shell scripts, web-platform integration and external API integrations.
