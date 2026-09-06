"""Token-bucket rate limiter for client-side send pacing.

Opt-in per call site: callers acquire before sending to stay under Meta
throughput limits. Thread-safe for sync use; async variant uses a lock.
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable


class RateLimiter:
    """Token-bucket limiter refilling at a fixed rate.

    Attributes:
        rate_per_second: Sustained token refill rate.
        capacity: Maximum burst tokens.
    """

    def __init__(
        self,
        rate_per_second: float,
        capacity: int,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleeper: Callable[[float], None] = time.sleep,
    ) -> None:
        """Initialize the limiter.

        Args:
            rate_per_second: Sustained token refill rate.
            capacity: Maximum burst tokens.
            clock: Monotonic clock (injectable for tests).
            sleeper: Sleep function (injectable for tests).
        """
        if rate_per_second <= 0:
            raise ValueError("rate_per_second must be positive.")
        if capacity <= 0:
            raise ValueError("capacity must be positive.")
        self.rate_per_second = rate_per_second
        self.capacity = capacity
        self._clock = clock
        self._sleeper = sleeper
        self._tokens = float(capacity)
        self._updated = clock()
        self._lock = threading.Lock()

    def _refill(self, now: float) -> None:
        """Add tokens earned since the last update.

        Args:
            now: Current clock reading.
        """
        elapsed = now - self._updated
        if elapsed > 0:
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate_per_second)
            self._updated = now

    def try_acquire(self, tokens: int = 1) -> bool:
        """Take tokens without waiting.

        Args:
            tokens: Tokens requested.

        Returns:
            True when tokens were available.
        """
        with self._lock:
            self._refill(self._clock())
            if self._tokens >= tokens:
                self._tokens -= tokens
                return True
            return False

    def wait_time(self, tokens: int = 1) -> float:
        """Compute seconds until tokens are available.

        Args:
            tokens: Tokens requested.

        Returns:
            Non-negative wait in seconds.
        """
        with self._lock:
            self._refill(self._clock())
            if self._tokens >= tokens:
                return 0.0
            return (tokens - self._tokens) / self.rate_per_second

    def acquire(self, tokens: int = 1) -> None:
        """Block until tokens are available, then take them.

        Args:
            tokens: Tokens requested.
        """
        while True:
            with self._lock:
                self._refill(self._clock())
                if self._tokens >= tokens:
                    self._tokens -= tokens
                    return
                wait = (tokens - self._tokens) / self.rate_per_second
            self._sleeper(wait)


class AsyncRateLimiter:
    """Async token-bucket limiter sharing sync semantics.

    Attributes:
        limiter: Underlying sync limiter for token accounting.
    """

    def __init__(self, rate_per_second: float, capacity: int) -> None:
        """Initialize the limiter.

        Args:
            rate_per_second: Sustained token refill rate.
            capacity: Maximum burst tokens.
        """
        self.limiter = RateLimiter(rate_per_second, capacity)
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """Wait until tokens are available, then take them.

        Args:
            tokens: Tokens requested.
        """
        while True:
            async with self._lock:
                if self.limiter.try_acquire(tokens):
                    return
                wait = self.limiter.wait_time(tokens)
            await asyncio.sleep(wait)


__all__ = ["AsyncRateLimiter", "RateLimiter"]
