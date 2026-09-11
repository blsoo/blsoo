# Architecture

```mermaid
flowchart LR
    U[URL] --> V[Target validation / SSRF guard]
    V --> F[HTTP fetch + safe redirects]
    F --> P[BeautifulSoup parser]
    P --> C1[CTA / form / FAQ]
    P --> C2[UTM / dates / key blocks]
    P --> C3[Link discovery]
    C3 --> L[Bounded link checks]
    C1 --> R[Readiness report]
    C2 --> R
    L --> R
    R --> UI[Web UI / JSON API]
```

## Design decisions

- **Server-side checker**: required for link status checks and consistent parsing.
- **Bounded crawler**: only one landing page plus at most 30 discovered links; this is preflight QA, not a crawler.
- **Manual Telegram layer**: business logic that depends on an authenticated Telegram/NotiBot session is reported as manual QA instead of pretending it can be verified from HTML.
- **Evidence-first output**: every check returns a status, short explanation and evidence so a technical specialist can quickly decide whether the launch is blocked.
- **Fail-safe URL handling**: redirects are revalidated and private/reserved network ranges are rejected.
