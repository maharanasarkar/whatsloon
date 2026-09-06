# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.0.0] - 2026-09-06

### Added

- v3 typed messaging: Pydantic models, builders, and canonical serializers for every 2.x sender type with legacy parity tests.
- `wa.messages` service on sync/async clients, including contextual replies via `reply_to`.
- `docs/messages.md` with the 2.x mapping table and `examples/v3_messages.py`.
- v3 webhook pipeline: HMAC verification, handshake, version-aware parsing with unknown preservation, fingerprint dedupe, routing/filters, sync/async/queued handling, FastAPI adapter, `docs/webhooks.md`, `examples/v3_webhooks.py`.
- v3 resources: media upload/download/delete (`wa.media`), template management and WABA/phone clients (`wa.templates`, `wa.business`), Flows endpoint encryption (`whatsloon[flows]`), `docs/resources.md`, examples.
- v3 reliability: token-bucket pacing, circuit breaker, bulk senders with per-item outcomes, OTel observability middleware (`whatsloon[observability]`), `docs/reliability.md`, `examples/v3_bulk.py`.
- v3 modern APIs: group management and group messaging (`wa.groups`), voice calling (`wa.calls`), BSUID/group/call webhook coverage, Direct Send tracking passthrough, `docs/modern.md`, `examples/v3_modern.py`.
- v3 ecosystem: testing fakes (`whatsloon.testing`), `whatsloon` CLI (init/doctor/send/webhook/template/flow/migrate), migration audit, `docs/ecosystem.md`.

## [2.0.5]

### Added

- Sync and async senders for text, media, template, interactive, and location messages.
- Custom client composition via mixins with `WhatsAppBaseClient`.
- Full test suite with coverage reporting.
- MkDocs Material documentation with API reference.
- Runnable examples with `.env.example`.
- CI matrix for Python 3.9-3.13, CodeQL, dependency review, docs deploy, and trusted-publishing release workflow.
- OSS standards: MIT license, code of conduct, contributing guide, security policy, issue templates, Dependabot, labeler, release drafter, funding, EditorConfig, pre-commit.

### Changed

- Modernized packaging to `pyproject.toml` with typed package and optional `test`, `dev`, and `docs` extras.
- Hardened `WhatsAppBaseClient` validation and normalization.
- **Breaking:** package moved to `src/` layout; version 3.0.0. The 2.x API remains available (top-level classes plus `whatsloon.compat` with deprecation warnings); per-send `to=` replaces pinned recipients in new code.

[Unreleased]: https://github.com/maharanasarkar/whatsloon/compare/v3.0.0...HEAD
[3.0.0]: https://github.com/maharanasarkar/whatsloon/compare/v2.0.5...v3.0.0
[2.0.5]: https://github.com/maharanasarkar/whatsloon/releases/tag/v2.0.5
