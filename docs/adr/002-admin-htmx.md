# ADR-002: Admin reference UI

Status: accepted
Date: 2026-09-06

## Context

Spec requires an optional admin console for conversations, messages, statuses, webhook events, and failures — not a CRM.

## Decision

- Reference stack: FastAPI/Starlette + server-rendered HTML + HTMX, no heavy JS build.
- Exposed via `whatsloon[admin]` extra; clean read-service boundary so a future React frontend can reuse it.
- Pluggable auth + RBAC/tenant scoping; PII masking on by default; raw payloads privileged + opt-in retention; never log/display secrets.

## Consequences

- Phase 1b ships SQL reference + admin views behind the extra.
- Admin tests cover auth, tenant isolation, pagination, redaction.
