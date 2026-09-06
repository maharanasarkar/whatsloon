"""Retention, anonymization, and idempotency policies."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any, Optional

from pydantic import BaseModel, Field

from whatsloon.persistence.models import Message, utcnow


def fingerprint(payload: dict[str, Any]) -> str:
    """Compute a stable fingerprint for webhook deduplication.

    Args:
        payload: Normalized event payload.

    Returns:
        Hex SHA-256 digest of canonical JSON.
    """
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class RetentionPolicy(BaseModel):
    """Data retention and privacy policy.

    Attributes:
        retention_days: Days before records expire; None keeps forever.
        retain_raw_payloads: Whether raw webhook payloads may be stored.
        anonymize_on_expiry: Whether expiry anonymizes instead of deleting.
    """

    retention_days: Optional[int] = Field(default=90, ge=1)
    retain_raw_payloads: bool = False
    anonymize_on_expiry: bool = True

    def expires_at(self, start: Optional[datetime] = None) -> Optional[datetime]:
        """Compute the expiry timestamp for a new record.

        Args:
            start: Base time; defaults to now.

        Returns:
            Expiry timestamp or None when retention is unlimited.
        """
        if self.retention_days is None:
            return None
        return (start or utcnow()) + timedelta(days=self.retention_days)

    def is_expired(self, message: Message, now: Optional[datetime] = None) -> bool:
        """Check whether a message exceeded retention.

        Args:
            message: Message record.
            now: Reference time; defaults to now.

        Returns:
            True when expired.
        """
        if message.retention_expires_at is None:
            return False
        return (now or utcnow()) >= message.retention_expires_at

    def anonymize(self, message: Message) -> Message:
        """Remove PII from a message while keeping operational metadata.

        Args:
            message: Message record.

        Returns:
            Copy with identifiers and content redacted.
        """
        updated = message.model_copy(deep=True)
        updated.sender = "redacted"
        updated.recipient = "redacted"
        updated.content_text = None
        updated.structured_payload = {}
        return updated


__all__ = ["RetentionPolicy", "fingerprint"]
