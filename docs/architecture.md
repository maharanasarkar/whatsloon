# Architecture (v3 target)

Layered design per the refactor spec:

```
Application / Bot / SaaS
  -> Public API (WhatsApp context client, wa.messages.send(to, ...), wa.graph.post escape hatch)
  -> Domain services (messages, media, templates, flows, business, phones, calls, groups)
  -> Typed models (Pydantic v2)
  -> Version adapters (registry: v19.0, v26.0, latest pinned)
  -> Shared transport (pooled httpx sync/async, timeouts, retry/backoff, tracing, error mapping)
  -> Meta Graph API
Sidecars (optional): persistence repos + SQL ref, admin (FastAPI+HTMX), framework/queue adapters,
observability (OTel/Prom/Sentry), testing fakes, CLI.
```

Rules: domain code is sync/async-agnostic; version diffs live in adapters only; all HTTP via
transport; no secret logging; unknown Meta fields preserved; Google docstrings everywhere.

See: `adr/001-pydantic-src-version-matrix.md`, `adr/002-admin-htmx.md`, `version-support.md`.
