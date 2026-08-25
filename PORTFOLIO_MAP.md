# Portfolio map

This page is the fastest way to review the portfolio depending on what you want to evaluate.

## 5-minute technical review

1. **DevWork** — start with the [README](https://github.com/blsoo/devwork-system-analysis), then follow one requirement through use case, API, SQL and tests.
2. **BullADM** — open the [repository](https://github.com/blsoo/bulladm-ops-automation), review the operation state machine, then risk/threat material.
3. **BullSignal** — open the [system architecture repository](https://github.com/blsoo/bullsignal-system-architecture), then reliability/freshness/deployment cases.
4. **JobRadar** — open the [repository](https://github.com/blsoo/jobradar-vacancy-intelligence) for a working external-API → scoring → persistence → Telegram workflow.
5. **SQL Casebook** — open the [repository](https://github.com/blsoo/sql-postgresql-casebook) for directly reviewable relational queries and learning progression.
6. **FlowBridge** — open the [repository](https://github.com/blsoo/flowbridge-integration-platform) for an enterprise-integration design from requirement to API/error/idempotency/test contracts.

## Evidence by skill

| Skill | Evidence |
|---|---|
| Requirements analysis | DevWork, BullADM, BullSignal and FlowBridge requirements |
| Business rules | DevWork/BullADM explicit rule sets; FlowBridge process/idempotency invariants; JobRadar scoring/application boundaries |
| SQL / relational model | SQL Casebook + DevWork ERD/PostgreSQL schema/examples + JobRadar decision persistence |
| REST / HTTP | DevWork API/OpenAPI; FlowBridge REST/OpenAPI/error contract; BullSignal integration contracts; JobRadar HH/Telegram integrations |
| Integration analysis | FlowBridge scenarios; DevWork integrations; BullSignal duplicate/freshness cases; JobRadar source/application boundaries |
| Sequence modelling | DevWork, BullADM, BullSignal, FlowBridge and JobRadar sequence diagrams |
| State modelling | task/action lifecycles, operation states, incidents, FlowBridge request delivery states and JobRadar application funnel |
| Failure analysis | stale state, duplicates, timeout ambiguity, verification failure, rollback and JobRadar fail-closed application state |
| Risk / threat analysis | BullADM risk register and public-safe threat model |
| Traceability | requirement → workflow/interface → verification matrices across the cases |
| CI/CD thinking | public GitHub Actions validators + deployment workflow modelling |
| Reliability | idempotency, fail-closed behaviour, availability/freshness separation, retry semantics and duplicate notification prevention |
| Change impact | DevWork recurring-task change request and issue-backed implementation plan |
| Engineering process | open roadmap issues with acceptance criteria instead of manufactured historical tickets |
| Product workflow | JobRadar: vacancy discovery → ranking → Telegram action → persisted decision/application intent |

## Portfolio structure

```mermaid
flowchart TD
    P[Profile] --> D[DevWork\nSystem analysis]
    P --> A[BullADM\nOperational safety]
    P --> B[BullSignal\nArchitecture & reliability]
    P --> J[JobRadar\nVacancy intelligence]
    P --> S[SQL Casebook\nSQL/PostgreSQL evidence]
    P --> F[FlowBridge\nEnterprise integrations]

    D --> R1[Requirements → API → DB → tests]
    A --> R2[Preflight → confirm → rollback]
    B --> R3[Idempotency → freshness → incidents]
    J --> R6[HH API → score → Telegram → feedback]
    S --> R4[PK/FK → filters → joins → roadmap]
    F --> R5[REST → idempotency → adapters → audit]
```

## Flagship projects

### DevWork

**Focus:** system analysis, requirements, domain/data modelling, REST/OpenAPI, SQL, integration behaviour, tests and traceability.

- [Repository](https://github.com/blsoo/devwork-system-analysis)
- [Roadmap](https://github.com/blsoo/devwork-system-analysis/blob/main/ROADMAP.md)
- [Open issues](https://github.com/blsoo/devwork-system-analysis/issues)

### BullADM

**Focus:** operational automation, safety gates, state machines, rollback, trust boundaries, risk/threat analysis and failure handling.

- [Repository](https://github.com/blsoo/bulladm-ops-automation)
- [Roadmap](https://github.com/blsoo/bulladm-ops-automation/blob/main/ROADMAP.md)
- [Open issues](https://github.com/blsoo/bulladm-ops-automation/issues)

### BullSignal

**Focus:** larger integration/reliability project: web/backend flows, Telegram, external APIs, background jobs, monitoring, freshness, deployment safety and research isolation.

Production implementation stays private; public material is deliberately sanitized.

- [Repository](https://github.com/blsoo/bullsignal-system-architecture)
- [Reliability cases](https://github.com/blsoo/bullsignal-system-architecture/blob/main/RELIABILITY_CASES.md)
- [Architecture diagrams](https://github.com/blsoo/bullsignal-system-architecture/blob/main/DIAGRAMS.md)
- [Roadmap](https://github.com/blsoo/bullsignal-system-architecture/blob/main/ROADMAP.md)

## Targeted technical cases

### JobRadar

**Focus:** a working vacancy-intelligence product: public HH search, normalization, explainable ranking, SQLite state, Telegram inline actions, truthful cover-letter preparation and an explicit OAuth boundary for real applications.

- [Repository](https://github.com/blsoo/jobradar-vacancy-intelligence)
- [Architecture](https://github.com/blsoo/jobradar-vacancy-intelligence/blob/main/ARCHITECTURE.md)
- [Open issues](https://github.com/blsoo/jobradar-vacancy-intelligence/issues)

### SQL & PostgreSQL Casebook

**Focus:** directly reviewable SQL knowledge with an explicit learning boundary: relational identity/relationships, filtering, NULL, ordering, counts and JOIN behaviour are demonstrated; more advanced SQL is roadmap work until mastered.

- [Repository](https://github.com/blsoo/sql-postgresql-casebook)
- [Challenges](https://github.com/blsoo/sql-postgresql-casebook/blob/main/CHALLENGES.md)
- [Learning log](https://github.com/blsoo/sql-postgresql-casebook/blob/main/LEARNING_LOG.md)
- [Open issues](https://github.com/blsoo/sql-postgresql-casebook/issues)

### FlowBridge

**Focus:** enterprise integration analysis: REST/HTTP contract, validation, PostgreSQL model, idempotency, retry/timeout behaviour, adapter boundaries and audit evidence.

The current repo is explicitly an analysis/design baseline; persistence, HTTP implementation and real adapter prototypes are tracked as next work.

- [Repository](https://github.com/blsoo/flowbridge-integration-platform)
- [OpenAPI](https://github.com/blsoo/flowbridge-integration-platform/blob/main/openapi.yaml)
- [Integration scenarios](https://github.com/blsoo/flowbridge-integration-platform/blob/main/INTEGRATION_SCENARIOS.md)
- [Open issues](https://github.com/blsoo/flowbridge-integration-platform/issues)
