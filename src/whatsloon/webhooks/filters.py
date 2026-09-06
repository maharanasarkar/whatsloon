"""Composable subscription filters for normalized events."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from whatsloon.webhooks.events import NormalizedEvent

Predicate = Callable[[NormalizedEvent], bool]
"""Custom event predicate."""


@dataclass
class SubscriptionFilter:
    """Decide whether a normalized event reaches a handler.

    Attributes:
        allow_types: Event types accepted; empty accepts all.
        deny_types: Event types rejected.
        allow_senders: Sender identifiers accepted; empty accepts all.
        predicate: Optional custom check applied last.
    """

    allow_types: set[str] = field(default_factory=set)
    deny_types: set[str] = field(default_factory=set)
    allow_senders: set[str] = field(default_factory=set)
    predicate: Predicate | None = None

    def matches(self, event: NormalizedEvent) -> bool:
        """Check an event against all configured rules.

        Args:
            event: Normalized event.

        Returns:
            True when the event should be handled.
        """
        if self.allow_types and event.event_type not in self.allow_types:
            return False
        if event.event_type in self.deny_types:
            return False
        sender = getattr(event, "sender", "")
        if self.allow_senders and sender not in self.allow_senders:
            return False
        if self.predicate is not None and not self.predicate(event):
            return False
        return True


__all__ = ["Predicate", "SubscriptionFilter"]
