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

    Accepts numeric seconds (``"7"``), millisecond suffixes (``"120ms"``),
    and HTTP dates (``"Thu, 01 Jan 2026 00:00:07 GMT"``) as seconds from now.

    Args:
        value: Header value.

    Returns:
        Seconds as float, or None when absent/unparseable.
    """
    if value is None:
        return None
    text = value.strip()
    lowered = text.lower()
    if lowered.endswith("ms"):
        try:
            parsed = float(lowered[:-2])
        except ValueError:
            return None
        return parsed / 1000.0 if parsed >= 0 else None
    try:
        parsed = float(text)
        return parsed if parsed >= 0 else None
    except (TypeError, ValueError):
        pass
    try:
        from datetime import datetime, timezone
        from email.utils import parsedate_to_datetime

        moment = parsedate_to_datetime(text)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=timezone.utc)
        delta = (moment - datetime.now(timezone.utc)).total_seconds()
        return max(0.0, delta)
    except (TypeError, ValueError, OverflowError):
        return None


def is_retryable_status(status_code: int) -> bool:
    """Decide whether an HTTP status is safe to retry.

    Args:
        status_code: HTTP status code.

    Returns:
        True for 429 and 5xx; False otherwise. Message POSTs with unknown
        outcome are handled by callers via idempotency keys.
    """
    return status_code == 429 or 500 <= status_code <= 599
