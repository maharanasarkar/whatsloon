"""Event routing to typed handlers with fallback support."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Optional

from whatsloon.webhooks.events import NormalizedEvent
from whatsloon.webhooks.filters import SubscriptionFilter

Handler = Callable[[NormalizedEvent], Any]
"""Synchronous event handler."""

AsyncHandler = Callable[[NormalizedEvent], Any]
"""Asynchronous event handler (awaited by the processor)."""


class EventRouter:
    """Dispatch normalized events to registered handlers.

    Attributes:
        handlers: Handlers keyed by event type.
        fallback: Handler for unregistered types including unknown.
    """

    def __init__(self) -> None:
        """Initialize an empty router."""
        self.handlers: dict[str, tuple[Handler, SubscriptionFilter]] = {}
        self.fallback: Optional[tuple[Handler, SubscriptionFilter]] = None

    def register(
        self, event_type: str, handler: Handler, filt: Optional[SubscriptionFilter] = None
    ) -> None:
        """Register a handler for an event type.

        Args:
            event_type: Normalized type such as ``"message.received"``.
            handler: Callable invoked with the event.
            filt: Optional subscription filter; unmatched events skip.
        """
        self.handlers[event_type] = (handler, filt or SubscriptionFilter())

    def set_fallback(self, handler: Handler, filt: Optional[SubscriptionFilter] = None) -> None:
        """Register the fallback for unregistered types.

        Args:
            handler: Callable invoked with the event.
            filt: Optional subscription filter.
        """
        self.fallback = (handler, filt or SubscriptionFilter())

    def resolve(self, event: NormalizedEvent) -> Optional[Handler]:
        """Resolve the handler for an event without invoking it.

        Args:
            event: Normalized event.

        Returns:
            Handler when registered and filter-passing, else None.

        Raises:
            UnsupportedEventError: If no handler or fallback applies.
        """
        from whatsloon.exceptions import UnsupportedEventError

        entry = self.handlers.get(event.event_type)
        if entry is not None:
            handler, filt = entry
            return handler if filt.matches(event) else None
        if self.fallback is not None:
            handler, filt = self.fallback
            return handler if filt.matches(event) else None
        raise UnsupportedEventError(f"No handler for event type {event.event_type!r}.")

    def dispatch(self, event: NormalizedEvent) -> Any:
        """Invoke the resolved handler for an event.

        Args:
            event: Normalized event.

        Returns:
            Handler return value, or None when filtered out.

        Raises:
            UnsupportedEventError: If no handler or fallback applies.
        """
        handler = self.resolve(event)
        if handler is None:
            return None
        return handler(event)


__all__ = ["AsyncHandler", "EventRouter", "Handler"]
