"""Bulk sender tests with stubbed services."""

from whatsloon.client import SendMessageResult
from whatsloon.messages.models import OutboundMessage, TextMessage
from whatsloon.reliability.bulk import AsyncBulkSender, BulkSender
from whatsloon.reliability.circuit import CircuitBreaker
from whatsloon.reliability.rate import RateLimiter


class StubService:
    """Message service double failing flagged recipients."""

    def __init__(self, fail=()) -> None:
        """Initialize with failing recipients.

        Args:
            fail: Recipients raising errors.
        """
        self.fail = set(fail)
        self.calls = []

    def send(self, envelope):
        """Record and answer or raise.

        Args:
            envelope: Outbound message.

        Returns:
            Canned result.
        """
        self.calls.append(envelope.to)
        if envelope.to in self.fail:
            raise RuntimeError(f"send failed for {envelope.to}")
        return SendMessageResult(message_id=f"id-{envelope.to}", to=envelope.to)


def _envelopes(*recipients):
    """Build text envelopes.

    Args:
        *recipients: Destination identifiers.

    Returns:
        Envelope list.
    """
    return [OutboundMessage(to=to, content=TextMessage(body="Hi")) for to in recipients]


def test_bulk_partial_failure_keeps_order():
    """Batches capture per-item failures without aborting."""
    sender = BulkSender(StubService(fail={"b"}), max_workers=2)
    summary = sender.send_all(_envelopes("a", "b", "c"))
    assert summary.sent == 2 and summary.failed == 1
    assert [item.to for item in summary.items] == ["a", "b", "c"]
    assert summary.items[1].ok is False and "send failed" in summary.items[1].error
    assert summary.items[0].message_id == "id-a"


def test_bulk_with_limiter_and_breaker():
    """Limiter and breaker compose around bulk sends."""
    limiter = RateLimiter(100.0, 10)
    breaker = CircuitBreaker(failure_threshold=10, cooldown_seconds=60.0)
    sender = BulkSender(StubService(), limiter=limiter, breaker=breaker, max_workers=1)
    summary = sender.send_all(_envelopes("a", "b"))
    assert summary.sent == 2


async def test_async_bulk_sender():
    """Async batches bound concurrency and preserve order."""

    class AsyncStub(StubService):
        async def send(self, envelope):
            return super().send(envelope)

    sender = AsyncBulkSender(AsyncStub(fail={"b"}), max_concurrency=2)
    summary = await sender.send_all(_envelopes("a", "b", "c"))
    assert summary.sent == 2 and summary.failed == 1
    assert [item.to for item in summary.items] == ["a", "b", "c"]
