# ADR-001: Pydantic v2, src layout, version matrix

Status: accepted
Date: 2026-09-06

## Context

Whatsloon 3 needs typed domain models, a clean `src/` packaging break with a `whatsloon.compat` 2.x shim, and pinned per-version Graph API adapters (`v19.0`, `v26.0`, `latest` alias).

## Decision

- Domain models use Pydantic v2 as a hard core dependency.
- Migrate to `src/whatsloon` layout in Phase 1a; keep flat package runnable until the compat shim lands.
- Ship adapters `v19_0` + `v26_0` first; `latest` resolves to the pinned `LATEST_VERSION` in code, never via network.
- Contract fixtures per adapter; version-matrix CI job.

## Consequences

- Core gains one hard dep (pydantic); SQL/admin stay optional extras.
- Phase 1a must add parity tests before deleting legacy mixins.
