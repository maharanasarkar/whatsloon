"""End-to-end pipeline tests: dedupe, failures, async, queue."""

from pathlib import Path

import pytest

from whatsloon.exceptions import InvalidSignatureError
from whatsloon.persistence.base import EventFilter
from whatsloon.persistence.models import ProcessingStatus
from whatsloon.persistence.repositories import InMemoryEventRepository
from whatsloon.webhooks.processor import WebhookProcessor
from whatsloon.webhooks.router import EventRouter
from whatsloon.webhooks.verifier import compute_signature

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "webhooks"
SECRET = "pipeline-secret"


def _body(name="message_received.json"):
    """Load a fixture body.

    Args:
        name: Fixture file name.

    Returns:
        Raw bytes.
    """
    return (FIXTURES / name).read_bytes()


def _processor(**kwargs):
    """Build a processor over in-memory storage.

    Args:
        **kwargs: WebhookProcessor overrides.

    Returns:
        Tuple of processor, router, event repository, and handled list.
    """
    router = EventRouter()
    events = InMemoryEventRepository()
    handled = []
    router.register("message.received", handled.append)
    kwargs.setdefault("router", router)
    kwargs.setdefault("events", events)
    kwargs.setdefault("tenant_resolver", lambda event: "t-1")
    processor = WebhookProcessor(**kwargs)
    return processor, router, events, handled


def _signed(body):
    """Sign a fixture body.

    Args:
        body: Raw bytes.

    Returns:
        Signature header value.
    """
    return compute_signature(SECRET, body)


def test_full_pipeline_handles_and_persists():
    """Verified deliveries run handlers and persist PROCESSED outcomes."""
    processor, _, events, handled = _processor()
    body = _body()
    results = processor.process(body, _signed(body), app_secret=SECRET)
    assert [r.outcome for r in results] == ["handled"]
    assert len(handled) == 1
    record = events.search(EventFilter(tenant_id="t-1"))[0]
    assert record.processing_status == ProcessingStatus.PROCESSED


def test_duplicate_delivery_handled_once():
    """Redeliveries dedupe to a single handler invocation."""
    processor, _, _, handled = _processor()
    body = _body()
    first = processor.process(body, _signed(body), app_secret=SECRET)
    second = processor.process(body, _signed(body), app_secret=SECRET)
    assert [r.outcome for r in first] == ["handled"]
    assert [r.outcome for r in second] == ["duplicate"]
    assert len(handled) == 1


def test_bad_signature_never_reaches_handlers():
    """Verification failures raise before parsing or persistence."""
    processor, _, events, handled = _processor()
    with pytest.raises(InvalidSignatureError):
        processor.process(_body(), "sha256=wrong", app_secret=SECRET)
    assert handled == []
    assert events.search(EventFilter(tenant_id="t-1")) == []


def test_handler_error_persists_failed():
    """Handler exceptions persist FAILED without losing the receipt."""
    router = EventRouter()
    events = InMemoryEventRepository()

    def boom(event):
        raise RuntimeError("downstream down")

    router.register("message.received", boom)
    processor = WebhookProcessor(router=router, events=events, tenant_resolver=lambda e: "t-1")
    results = processor.process(_body(), _signed(_body()), app_secret=SECRET)
    assert results[0].outcome == "failed"
    record = events.search(EventFilter(tenant_id="t-1"))[0]
    assert record.processing_status == ProcessingStatus.FAILED
    assert "downstream" in (record.error_summary or "")


def test_queue_hook_defers_handling():
    """Configured queues defer handling and mark events retryable."""
    queued = []
    processor, _, events, handled = _processor(queue=queued.append)
    results = processor.process(_body(), _signed(_body()), app_secret=SECRET)
    assert results[0].outcome == "queued"
    assert handled == [] and len(queued) == 1
    record = events.search(EventFilter(tenant_id="t-1"))[0]
    assert record.processing_status == ProcessingStatus.RETRYING


async def test_async_handlers_awaited():
    """Coroutine handlers run on the async path."""
    router = EventRouter()
    events = InMemoryEventRepository()
    seen = []

    async def handler(event):
        seen.append(event.message_id)

    router.register("message.received", handler)
    processor = WebhookProcessor(router=router, events=events, tenant_resolver=lambda e: "t-1")
    results = await processor.aprocess(_body(), _signed(_body()), app_secret=SECRET)
    assert results[0].outcome == "handled"
    assert seen == ["wamid.fixture-msg-1"]
