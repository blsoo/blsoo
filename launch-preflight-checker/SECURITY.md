# Security notes

Launch Preflight Checker fetches user-supplied URLs server-side, so SSRF is the main threat model.

Implemented guardrails:

- only `http` / `https` schemes;
- URLs with embedded credentials are rejected;
- DNS must resolve only to globally routable addresses;
- every redirect target is validated again;
- redirect depth, request time and HTML body size are bounded;
- link checks are capped at 30 URLs.

This is a small launch-QA utility, not a hardened multi-tenant crawler. For public Internet deployment, run it in an isolated container with restricted egress and rate limiting at the reverse proxy.
