"""Retry helpers shared by sync and async transports."""

from __future__ import annotations

import random
from typing import Optional

from whatsloon.config.settings import RetryConfig


def backoff_delay(attempt: int, policy: RetryConfig) -> float:
    """Compute exponential backoff with optional jitter.

    Args:
        attempt: Zero-based retry index (0 is the first retry).
        policy: Retry policy.

    Returns:
        Seconds to wait before the next attempt, capped by the policy.
    """
    delay: float = min(policy.backoff_base * (2**attempt), policy.backoff_cap)
    if policy.jitter:
        delay = float(random.uniform(0, delay))
    return delay


def parse_retry_after(value: Optional[str]) -> Optional[float]:
    """Parse a Meta ``Retry-After`` header value.

    Args:
        value: Header value in seconds.

    Returns:
        Seconds as float, or None when absent/unparseable.
    """
    if value is None:
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def is_retryable_status(status_code: int) -> bool:
    """Decide whether an HTTP status is safe to retry.

    Args:
        status_code: HTTP status code.

    Returns:
        True for 429 and 5xx; False otherwise. Message POSTs with unknown
        outcome are handled by callers via idempotency keys.
    """
    return status_code == 429 or 500 <= status_code <= 599
