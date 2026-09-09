"""In-memory repository implementations.

Zero-dependency stores for tests, local development, and embedding. All
operations enforce tenant isolation; duplicate idempotency keys and event
hashes return the original record.
"""

from __future__ import annotations

from typing import Optional

from whatsloon.persistence.base import (
    ConversationRepository,
    EventFilter,
    EventRepository,
    MediaRepository,
    MessageFilter,
    MessageRepository,
)
from whatsloon.persistence.models import (
    Conversation,
    MediaMetadata,
    Message,
    MessageStatus,
    WebhookEvent,
)


def _matches_message(message: Message, query: MessageFilter) -> bool:
    """Check a message against a filter.

    Args:
        message: Candidate record.
        query: Search filter.

    Returns:
        True when all set fields match.
    """
    if message.tenant_id != query.tenant_id:
        return False
    if query.conversation_id and message.conversation_id != query.conversation_id:
        return False
    if query.direction and message.direction.value != query.direction:
        return False
    if query.message_type and message.message_type != query.message_type:
        return False
    if query.status and message.status != query.status:
        return False
    if query.sender and message.sender != query.sender:
        return False
    if (
        query.content_contains
        and query.content_contains.lower() not in (message.content_text or "").lower()
    ):
        return False
    if query.since and message.created_at < query.since:
        return False
    if query.until and message.created_at >= query.until:
        return False
    return True


class InMemoryConversationRepository(ConversationRepository):
    """Dictionary-backed conversation store."""

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._items: dict[tuple[str, str], Conversation] = {}

    def upsert(self, conversation: Conversation) -> Conversation:
        """Insert or update by ``(tenant_id, external_chat_id)``.

        Args:
            conversation: Conversation record.

        Returns:
            Stored record.
        """
        key = (conversation.tenant_id, conversation.external_chat_id)
        existing = self._items.get(key)
        if existing is not None:
            merged = existing.model_copy(update=conversation.model_dump(exclude={"id"}))
            merged.id = existing.id
            self._items[key] = merged
            return merged
        self._items[key] = conversation
        return conversation

    def get(self, tenant_id: str, conversation_id: str) -> Optional[Conversation]:
        """Fetch one conversation within a tenant.

        Args:
            tenant_id: Owning tenant.
            conversation_id: Local identifier.

        Returns:
            Record or None.
        """
        for item in self._items.values():
            if item.tenant_id == tenant_id and item.id == conversation_id:
                return item
        return None

    def list(self, tenant_id: str, limit: int = 50, offset: int = 0) -> list[Conversation]:
        """List conversations for a tenant, newest activity first.

        Args:
            tenant_id: Owning tenant.
            limit: Maximum rows.
            offset: Rows to skip.

        Returns:
            Matching records.
        """
        items = [c for c in self._items.values() if c.tenant_id == tenant_id]
        items.sort(key=lambda c: c.last_activity_at, reverse=True)
        return items[offset : offset + limit]


class InMemoryMessageRepository(MessageRepository):
    """Dictionary-backed message store with idempotent writes."""

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._items: dict[str, Message] = {}
        self._by_key: dict[tuple[str, str], str] = {}
        self._statuses: dict[str, list[MessageStatus]] = {}

    def save(self, message: Message) -> Message:
        """Insert a message; duplicate idempotency keys return the original.

        Args:
            message: Message record.

        Returns:
            Stored (or previously stored) record.
        """
        if message.idempotency_key:
            key = (message.tenant_id, message.idempotency_key)
            existing_id = self._by_key.get(key)
            if existing_id is not None:
                return self._items[existing_id]
            self._by_key[key] = message.id
        self._items[message.id] = message
        return message

    def get(self, tenant_id: str, message_id: str) -> Optional[Message]:
        """Fetch one message within a tenant.

        Args:
            tenant_id: Owning tenant.
            message_id: Local identifier.

        Returns:
            Record or None.
        """
        item = self._items.get(message_id)
        if item is None or item.tenant_id != tenant_id:
            return None
        return item

    def search(self, query: MessageFilter) -> list[Message]:
        """Search messages honoring tenant isolation.

        Args:
            query: Search filter.

        Returns:
            Matching records newest first.
        """
        items = [m for m in self._items.values() if _matches_message(m, query)]
        items.sort(key=lambda m: m.created_at, reverse=True)
        return items[query.offset : query.offset + query.limit]

    def save_status(self, status: MessageStatus) -> MessageStatus:
        """Append a delivery status transition.

        Args:
            status: Status record.

        Returns:
            Stored record.
        """
        self._statuses.setdefault(status.message_id, []).append(status)
        message = self._items.get(status.message_id)
        if message is not None and message.tenant_id == status.tenant_id:
            message.status = status.external_status
        return status

    def statuses(self, tenant_id: str, message_id: str) -> list[MessageStatus]:
        """List status transitions for a message.

        Args:
            tenant_id: Owning tenant.
            message_id: Local identifier.

        Returns:
            Status records in occurrence order.
        """
        message = self._items.get(message_id)
        if message is None or message.tenant_id != tenant_id:
            return []
        return list(self._statuses.get(message_id, []))


class InMemoryEventRepository(EventRepository):
    """Dictionary-backed webhook event store with hash dedupe."""

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._items: dict[str, WebhookEvent] = {}
        self._by_hash: dict[tuple[str, str], str] = {}
        self._raw: dict[str, dict] = {}

    def record(self, event: WebhookEvent, raw_payload: Optional[dict] = None) -> WebhookEvent:
        """Record receipt; known hashes return the original event.

        Args:
            event: Event record.
            raw_payload: Optional raw payload when retention allows.

        Returns:
            Stored (or previously stored) record.
        """
        key = (event.tenant_id, event.event_hash)
        existing_id = self._by_hash.get(key)
        if existing_id is not None:
            return self._items[existing_id]
        self._by_hash[key] = event.id
        self._items[event.id] = event
        if raw_payload is not None and event.has_raw_payload:
            self._raw[event.id] = raw_payload
        return event

    def get_by_hash(self, tenant_id: str, event_hash: str) -> Optional[WebhookEvent]:
        """Fetch an event by fingerprint within a tenant.

        Args:
            tenant_id: Owning tenant.
            event_hash: Event fingerprint.

        Returns:
            Record or None.
        """
        event_id = self._by_hash.get((tenant_id, event_hash))
        return self._items.get(event_id) if event_id else None

    def search(self, query: EventFilter) -> list[WebhookEvent]:
        """Search events honoring tenant isolation.

        Args:
            query: Search filter.

        Returns:
            Matching records newest first.
        """
        items = [e for e in self._items.values() if e.tenant_id == query.tenant_id]
        if query.event_type:
            items = [e for e in items if e.event_type == query.event_type]
        if query.processing_status:
            items = [e for e in items if e.processing_status.value == query.processing_status]
        if query.since:
            items = [e for e in items if e.received_at >= query.since]
        if query.until:
            items = [e for e in items if e.received_at < query.until]
        items.sort(key=lambda e: e.received_at, reverse=True)
        return items[query.offset : query.offset + query.limit]

    def mark(self, event: WebhookEvent) -> WebhookEvent:
        """Persist a processing outcome.

        Args:
            event: Updated event record.

        Returns:
            Stored record.
        """
        self._items[event.id] = event
        return event

    def raw_payload(self, tenant_id: str, event_id: str) -> Optional[dict]:
        """Fetch a retained raw payload within a tenant.

        Args:
            tenant_id: Owning tenant.
            event_id: Local identifier.

        Returns:
            Raw payload or None.
        """
        event = self._items.get(event_id)
        if event is None or event.tenant_id != tenant_id:
            return None
        return self._raw.get(event_id)


class InMemoryMediaRepository(MediaRepository):
    """Dictionary-backed media metadata store."""

    def __init__(self) -> None:
        """Initialize empty storage."""
        self._items: dict[str, MediaMetadata] = {}
        self._by_external: dict[tuple[str, str], str] = {}

    def save(self, media: MediaMetadata) -> MediaMetadata:
        """Store a media descriptor idempotently by external ID.

        Args:
            media: Media record.

        Returns:
            Stored (or previously stored) record.
        """
        key = (media.tenant_id, media.external_media_id)
        existing_id = self._by_external.get(key)
        if existing_id is not None:
            return self._items[existing_id]
        self._by_external[key] = media.id
        self._items[media.id] = media
        return media

    def get(self, tenant_id: str, media_id: str) -> Optional[MediaMetadata]:
        """Fetch a media descriptor within a tenant.

        Args:
            tenant_id: Owning tenant.
            media_id: Local identifier.

        Returns:
            Record or None.
        """
        item = self._items.get(media_id)
        if item is None or item.tenant_id != tenant_id:
            return None
        return item


__all__ = [
    "InMemoryConversationRepository",
    "InMemoryEventRepository",
    "InMemoryMediaRepository",
    "InMemoryMessageRepository",
]
