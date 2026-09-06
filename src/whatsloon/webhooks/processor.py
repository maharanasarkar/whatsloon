"""End-to-end webhook pipeline.

Pipeline order: raw bytes -> HMAC verify -> parse -> fingerprint/dedupe ->
persist receipt -> route/filter -> handle (sync|async|queued) -> persist
result -> ack summary. Receipts persist before handling so redeliveries are
safe; handler failures persist as FAILED without losing sibling events.
"""

from __future__ import annotations

import asyncio
import inspect
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Optional

from whatsloon.persistence.models import ProcessingStatus, WebhookEvent, utcnow
from whatsloon.persistence.policies import fingerprint
from whatsloon.webhooks.events import NormalizedEvent
from whatsloon.webhooks.parser import parse_body
from whatsloon.webhooks.router import EventRouter
from whatsloon.webhooks.verifier import verify_signature

TenantResolver = Callable[[NormalizedEvent], str]
"""Resolve the owning tenant for a normalized event."""

EnqueueHook = Callable[[str], None]
"""Queue a stored event ID for background handling."""


def default_tenant_resolver(event: NormalizedEvent) -> str:
    """Resolve tenants by recipient phone ID with a default fallback.

    Args:
        event: Normalized event.

    Returns:
        Recipient phone ID or ``"default"``.
    """
    phone_id = getattr(event, "recipient_phone_id", "")
    return phone_id or "default"


def _run_awaitable_sync(awaitable: Any) -> Any:
    """Drive a coroutine handler from the sync pipeline.

    Args:
        awaitable: Coroutine returned by a handler.

    Returns:
        Handler result.

    Raises:
        RuntimeError: If called inside a running event loop; use
            :meth:`WebhookProcessor.aprocess` instead.
    """
    try:
        asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(awaitable)
    awaitable.close()
    raise RuntimeError("Async handler in sync process(); use aprocess() instead.")


@dataclass
class ProcessResult:
    """Outcome for one normalized event.

    Attributes:
        event_id: Stored event identifier.
        event_type: Normalized type.
        outcome: One of handled, duplicate, filtered, failed, queued.
        detail: Redacted detail such as an error summary.
    """

    event_id: str
    event_type: str
    outcome: str
    detail: str = ""


@dataclass
class WebhookProcessor:
    """Execute the inbound pipeline over repository storage.

    Attributes:
        router: Event router with registered handlers.
        events: Event repository for receipts and outcomes.
        tenant_resolver: Tenant mapping for normalized events.
        api_version: Adapter version stamp for parsing.
        retain_raw: Whether to retain raw payloads (opt-in).
        queue: Optional enqueue hook; when set, handling is deferred.
    """

    router: EventRouter
    events: Any
    tenant_resolver: TenantResolver = default_tenant_resolver
    api_version: str = ""
    retain_raw: bool = False
    queue: Optional[EnqueueHook] = None

    def process(
        self, raw_body: bytes, signature_header: Optional[str], *, app_secret: Any
    ) -> list[ProcessResult]:
        """Verify, parse, dedupe, persist, and handle one delivery.

        Args:
            raw_body: Raw request bytes exactly as received.
            signature_header: Value of ``X-Hub-Signature-256``.
            app_secret: Configured app secret (never logged).

        Returns:
            Per-event outcomes. Callers ack to Meta once returned.

        Raises:
            ConfigurationError: If verification is unconfigured.
            InvalidSignatureError: If verification fails.
            InvalidPayloadError: If the body is malformed.
        """
        verify_signature(app_secret, raw_body, signature_header)
        results: list[ProcessResult] = []
        for event in parse_body(raw_body, api_version=self.api_version):
            results.append(self._handle_one(event))
        return results

    async def aprocess(
        self, raw_body: bytes, signature_header: Optional[str], *, app_secret: Any
    ) -> list[ProcessResult]:
        """Async variant awaiting coroutine handlers.

        Args:
            raw_body: Raw request bytes exactly as received.
            signature_header: Value of ``X-Hub-Signature-256``.
            app_secret: Configured app secret (never logged).

        Returns:
            Per-event outcomes.

        Raises:
            ConfigurationError: If verification is unconfigured.
            InvalidSignatureError: If verification fails.
            InvalidPayloadError: If the body is malformed.
        """
        verify_signature(app_secret, raw_body, signature_header)
        results: list[ProcessResult] = []
        for event in parse_body(raw_body, api_version=self.api_version):
            results.append(await self._ahandle_one(event))
        return results

    def _store_receipt(self, event: NormalizedEvent) -> tuple[Any, bool]:
        """Persist receipt, returning the record and duplicate flag.

        Args:
            event: Normalized event.

        Returns:
            Tuple of stored record and whether it was already known.
        """
        tenant_id = self.tenant_resolver(event)
        event_hash = fingerprint(event.model_dump())
        known = self.events.get_by_hash(tenant_id, event_hash)
        if known is not None:
            return known, True
        record = WebhookEvent(
            id=uuid.uuid4().hex,
            event_hash=event_hash,
            tenant_id=tenant_id,
            event_type=event.event_type,
            has_raw_payload=self.retain_raw,
        )
        raw = event.model_dump() if self.retain_raw else None
        return self.events.record(record, raw), False

    def _finish(self, record: Any, *, status: ProcessingStatus, error: str = "") -> None:
        """Persist a processing outcome.

        Args:
            record: Stored event record.
            status: Outcome status.
            error: Redacted error summary.
        """
        record.processing_status = status
        record.processed_at = utcnow()
        if error:
            record.error_summary = error[:500]
        self.events.mark(record)

    def _handle_one(self, event: NormalizedEvent) -> ProcessResult:
        """Handle one normalized event synchronously.

        Args:
            event: Normalized event.

        Returns:
            Outcome record.
        """
        record, duplicate = self._store_receipt(event)
        if duplicate and record.processing_status == ProcessingStatus.PROCESSED:
            return ProcessResult(record.id, event.event_type, "duplicate")
        if self.queue is not None:
            self.queue(record.id)
            self._finish(record, status=ProcessingStatus.RETRYING)
            return ProcessResult(record.id, event.event_type, "queued")
        try:
            handler = self.router.resolve(event)
        except Exception as exc:
            self._finish(record, status=ProcessingStatus.FAILED, error=str(exc))
            return ProcessResult(record.id, event.event_type, "failed", str(exc)[:200])
        if handler is None:
            self._finish(record, status=ProcessingStatus.PROCESSED)
            return ProcessResult(record.id, event.event_type, "filtered")
        try:
            outcome = handler(event)
            if inspect.isawaitable(outcome):
                outcome = _run_awaitable_sync(outcome)
            self._finish(record, status=ProcessingStatus.PROCESSED)
            return ProcessResult(record.id, event.event_type, "handled")
        except Exception as exc:
            self._finish(record, status=ProcessingStatus.FAILED, error=str(exc))
            return ProcessResult(record.id, event.event_type, "failed", str(exc)[:200])

    async def _ahandle_one(self, event: NormalizedEvent) -> ProcessResult:
        """Handle one normalized event with async support.

        Args:
            event: Normalized event.

        Returns:
            Outcome record.
        """
        record, duplicate = self._store_receipt(event)
        if duplicate and record.processing_status == ProcessingStatus.PROCESSED:
            return ProcessResult(record.id, event.event_type, "duplicate")
        if self.queue is not None:
            self.queue(record.id)
            self._finish(record, status=ProcessingStatus.RETRYING)
            return ProcessResult(record.id, event.event_type, "queued")
        try:
            handler = self.router.resolve(event)
        except Exception as exc:
            self._finish(record, status=ProcessingStatus.FAILED, error=str(exc))
            return ProcessResult(record.id, event.event_type, "failed", str(exc)[:200])
        if handler is None:
            self._finish(record, status=ProcessingStatus.PROCESSED)
            return ProcessResult(record.id, event.event_type, "filtered")
        try:
            outcome = handler(event)
            if inspect.isawaitable(outcome):
                await outcome
            self._finish(record, status=ProcessingStatus.PROCESSED)
            return ProcessResult(record.id, event.event_type, "handled")
        except Exception as exc:
            self._finish(record, status=ProcessingStatus.FAILED, error=str(exc))
            return ProcessResult(record.id, event.event_type, "failed", str(exc)[:200])


__all__ = [
    "EnqueueHook",
    "ProcessResult",
    "TenantResolver",
    "WebhookProcessor",
    "default_tenant_resolver",
]
