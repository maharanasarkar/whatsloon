"""Circuit breaker for failing downstream calls.

States: closed (normal), open (failing fast), half-open (single trial).
Only transport and server errors count; validation and auth failures pass
through without tripping the breaker.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from enum import Enum
from typing import Any

from whatsloon.exceptions import APIError, TransportError, WhatsAppError


class CircuitState(str, Enum):
    """Breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(WhatsAppError):
    """Raised when calls fail fast while the circuit is open."""


def _counts_toward_breaker(exc: BaseException) -> bool:
    """Decide whether a failure indicates downstream trouble.

    Args:
        exc: The failure.

    Returns:
        True for transport errors and retryable API errors only.
    """
    if isinstance(exc, TransportError):
        return exc.retryable
    if isinstance(exc, APIError):
        return exc.retryable
    return False


class CircuitBreaker:
    """Thread-safe circuit breaker around fallible calls.

    Attributes:
        failure_threshold: Consecutive counted failures to trip.
        cooldown_seconds: Open-state wait before a trial.
        state: Current state.
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        cooldown_seconds: float = 30.0,
        *,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        """Initialize the breaker.

        Args:
            failure_threshold: Consecutive counted failures to trip.
            cooldown_seconds: Open-state wait before a trial.
            clock: Monotonic clock (injectable for tests).
        """
        if failure_threshold <= 0:
            raise ValueError("failure_threshold must be positive.")
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self._clock = clock
        self._lock = threading.Lock()
        self._state = CircuitState.CLOSED
        self._failures = 0
        self._opened_at = 0.0

    @property
    def state(self) -> CircuitState:
        """Return the current state, promoting to half-open after cooldown.

        Returns:
            Current circuit state.
        """
        with self._lock:
            if (
                self._state == CircuitState.OPEN
                and self._clock() - self._opened_at >= self.cooldown_seconds
            ):
                self._state = CircuitState.HALF_OPEN
            return self._state

    def call(self, func: Callable[[], Any]) -> Any:
        """Execute a call through the breaker.

        Args:
            func: Zero-argument callable.

        Returns:
            Callable return value.

        Raises:
            CircuitOpenError: If the circuit is open.
            Exception: Whatever the callable raises.
        """
        if self.state == CircuitState.OPEN:
            raise CircuitOpenError("Circuit is open; failing fast.")
        try:
            result = func()
        except BaseException as exc:
            self._record_failure(exc)
            raise
        self._record_success()
        return result

    def _record_failure(self, exc: BaseException) -> None:
        """Record a failure, tripping when the threshold is reached.

        Args:
            exc: The failure.
        """
        if not _counts_toward_breaker(exc):
            return
        with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.OPEN
                self._opened_at = self._clock()
                return
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._state = CircuitState.OPEN
                self._opened_at = self._clock()

    def _record_success(self) -> None:
        """Reset the breaker on success."""
        with self._lock:
            self._failures = 0
            self._state = CircuitState.CLOSED


__all__ = ["CircuitBreaker", "CircuitOpenError", "CircuitState"]
