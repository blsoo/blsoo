# BullSignal diagrams

Public-safe diagrams for discussing system boundaries, reliability and integration design. Real production topology, credentials, provider details, private endpoints and trading rules are intentionally excluded.

## 1. High-level architecture

```mermaid
flowchart LR
    U[User] --> WEB[Web UI]
    U --> TG[Telegram UI]
    WEB --> APP[Application Backend]
    TG --> APP
    APP --> DB[(Application Data)]
    APP --> EXT[External APIs]
    APP --> JOBS[Background Jobs]
    JOBS --> EXT
    JOBS --> CACHE[(Runtime / Cache State)]
    APP --> MON[Monitoring / Health]
    JOBS --> MON
    RES[Research Analytics] --> DATA[(Research Data)]
    RES -. isolated from live actions .-> APP
```

The portfolio describes responsibilities and boundaries, not real host placement.

## 2. Telegram callback with duplicate protection

```mermaid
sequenceDiagram
    actor User
    participant TG as Telegram
    participant API as Callback Handler
    participant Guard as Idempotency Guard
    participant Service as Application Service
    participant DB as Storage

    User->>TG: presses action
    TG->>API: callback event
    API->>Guard: check event/action key
    alt already processed
        Guard-->>API: duplicate
        API-->>TG: acknowledge without repeating side effect
    else new event
        Guard-->>API: allowed
        API->>Service: execute action
        Service->>DB: persist state
        DB-->>Service: committed
        Service-->>API: result
        API->>Guard: mark completed
        API-->>TG: response
    end
```

## 3. Data freshness contract

```mermaid
flowchart TD
    A[Data source] --> B[Collector / Job]
    B --> C[(Cache / Storage)]
    C --> D{Data exists?}
    D -- No --> X[Unavailable state]
    D -- Yes --> E{Fresh enough?}
    E -- No --> Y[Stale state]
    E -- Yes --> F[API response]
    F --> G{Frontend rendered?}
    G -- No --> Z[UI error state]
    G -- Yes --> H[Healthy user-visible state]
```

A successful HTTP response alone is not considered proof that the user sees fresh data.

## 4. Confirmation-gated action

```mermaid
stateDiagram-v2
    [*] --> prepared
    prepared --> awaiting_confirmation: validation passed
    prepared --> rejected: validation failed
    awaiting_confirmation --> cancelled: user cancels / expires
    awaiting_confirmation --> executing: explicit confirm
    executing --> completed: side effect verified
    executing --> failed: execution/verification error
    failed --> rollback_required: recoverable change
    rollback_required --> rolled_back: rollback succeeds
    completed --> [*]
    rejected --> [*]
    cancelled --> [*]
    rolled_back --> [*]
```

## 5. Deployment safety flow

```mermaid
flowchart LR
    C[Change] --> I[Inspect]
    I --> B[Verify baseline]
    B --> BK[Create backup/checkpoint]
    BK --> A[Apply minimal change]
    A --> V[Verification]
    V -->|pass| S[Success]
    V -->|fail| R[Rollback]
    R --> RV[Verify recovery]
```

## 6. Monitoring / incident lifecycle

```mermaid
stateDiagram-v2
    [*] --> healthy
    healthy --> degraded: warning detected
    healthy --> incident: critical failure
    degraded --> healthy: recovered
    degraded --> incident: escalation
    incident --> investigating: acknowledged
    investigating --> recovering: remediation selected
    recovering --> healthy: verification passed
    recovering --> investigating: verification failed
```

## 7. Research isolation

```mermaid
flowchart LR
    SRC[Historical / collected data] --> LAB[Research Pipeline]
    LAB --> EXP[Experiments]
    EXP --> MET[Evaluation / Audit Evidence]
    MET --> DEC{Promote idea?}
    DEC -- No --> LAB
    DEC -- Review only --> DOC[Documented candidate]
    DOC -. no automatic live activation .-> PROD[Production Application]
```

## Interview talking points

- Why idempotency is an integration requirement, not a Telegram-specific hack.
- Why freshness and availability are different states.
- Why rollback belongs in deployment design before an incident happens.
- Where user-facing interfaces end and application services begin.
- Why research code is isolated from live side effects.
- How monitoring states help distinguish warning, incident, recovery and verification.
