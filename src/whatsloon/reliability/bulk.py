"""Bulk sends with per-item outcomes over message services.

Batches never abort on single failures: each envelope resolves to a
:class:`BulkItemResult` and the batch summary reports totals. Optional
rate limiting and circuit breaking compose per item.
"""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Any as _Any
from typing import Optional

from whatsloon.messages.models import OutboundMessage
from whatsloon.reliability.circuit import CircuitBreaker
from whatsloon.reliability.rate import AsyncRateLimiter, RateLimiter


@dataclass
class BulkItemResult:
    """Outcome for one envelope in a batch.

    Attributes:
        index: Position in the submitted batch.
        to: Destination identifier.
        ok: Whether the send succeeded.
        message_id: Meta identifier on success.
        error: Redacted error summary on failure.
    """

    index: int
    to: str
    ok: bool
    message_id: str = ""
    error: str = ""


@dataclass
class BulkSummary:
    """Aggregate batch outcome.

    Attributes:
        items: Per-item results in submission order.
        sent: Successful count.
        failed: Failure count.
    """

    items: list[BulkItemResult] = field(default_factory=list)

    @property
    def sent(self) -> int:
        """Count successful sends.

        Returns:
            Success count.
        """
        return sum(1 for item in self.items if item.ok)

    @property
    def failed(self) -> int:
        """Count failed sends.

        Returns:
            Failure count.
        """
        return sum(1 for item in self.items if not item.ok)


class BulkSender:
    """Synchronous bulk sends with bounded concurrency.

    Attributes:
        service: Message service executing individual sends.
        max_workers: Thread pool size.
        limiter: Optional rate limiter applied per item.
        breaker: Optional circuit breaker wrapping per-item sends.
    """

    def __init__(
        self,
        service: _Any,
        *,
        max_workers: int = 5,
        limiter: Optional[RateLimiter] = None,
        breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        """Initialize the bulk sender.

        Args:
            service: Message service executing individual sends.
            max_workers: Thread pool size.
            limiter: Optional rate limiter applied per item.
            breaker: Optional circuit breaker wrapping per-item sends.
        """
        self.service = service
        self.max_workers = max_workers
        self.limiter = limiter
        self.breaker = breaker

    def _send_one(self, index: int, envelope: OutboundMessage) -> BulkItemResult:
        """Send one envelope, capturing failures per item.

        Args:
            index: Position in the batch.
            envelope: Outbound message.

        Returns:
            Item result; never raises for send failures.
        """
        try:
            if self.limiter is not None:
                self.limiter.acquire()
            if self.breaker is not None:
                result = self.breaker.call(lambda: self.service.send(envelope))
            else:
                result = self.service.send(envelope)
            return BulkItemResult(
                index=index, to=envelope.to, ok=True, message_id=result.message_id or ""
            )
        except Exception as exc:
            return BulkItemResult(index=index, to=envelope.to, ok=False, error=str(exc)[:300])

    def send_all(self, envelopes: list[OutboundMessage]) -> BulkSummary:
        """Send a batch preserving submission order in results.

        Args:
            envelopes: Outbound messages.

        Returns:
            Summary with per-item outcomes.
        """
        with ThreadPoolExecutor(max_workers=self.max_workers) as pool:
            items = list(pool.map(self._send_one, range(len(envelopes)), envelopes))
        items.sort(key=lambda item: item.index)
        return BulkSummary(items=items)


class AsyncBulkSender:
    """Asynchronous bulk sends with bounded concurrency.

    Attributes:
        service: Async message service.
        max_concurrency: Semaphore bound.
        limiter: Optional async rate limiter applied per item.
    """

    def __init__(
        self,
        service: _Any,
        *,
        max_concurrency: int = 10,
        limiter: Optional[AsyncRateLimiter] = None,
    ) -> None:
        """Initialize the async bulk sender.

        Args:
            service: Async message service.
            max_concurrency: Semaphore bound.
            limiter: Optional async rate limiter applied per item.
        """
        self.service = service
        self.max_concurrency = max_concurrency
        self.limiter = limiter

    async def send_all(self, envelopes: list[OutboundMessage]) -> BulkSummary:
        """Send a batch preserving submission order in results.

        Args:
            envelopes: Outbound messages.

        Returns:
            Summary with per-item outcomes.
        """
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _one(index: int, envelope: OutboundMessage) -> BulkItemResult:
            async with semaphore:
                try:
                    if self.limiter is not None:
                        await self.limiter.acquire()
                    result = await self.service.send(envelope)
                    return BulkItemResult(
                        index=index, to=envelope.to, ok=True, message_id=result.message_id or ""
                    )
                except Exception as exc:
                    return BulkItemResult(
                        index=index, to=envelope.to, ok=False, error=str(exc)[:300]
                    )

        items = await asyncio.gather(*[_one(index, env) for index, env in enumerate(envelopes)])
        return BulkSummary(items=sorted(items, key=lambda item: item.index))


__all__ = ["AsyncBulkSender", "BulkItemResult", "BulkSender", "BulkSummary"]
