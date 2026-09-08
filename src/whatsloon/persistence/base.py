"""Repository interfaces for message/event storage.

Implementations must scope every operation by tenant and treat duplicate
idempotency keys and event hashes as safe no-ops.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Protocol

from whatsloon.persistence.models import (
    Conversation,
    MediaMetadata,
    Message,
    MessageStatus,
    WebhookEvent,
)


@dataclass
class MessageFilter:
    """Query filter for message searches.

    Attributes:
        tenant_id: Owning tenant (required for isolation).
        conversation_id: Restrict to one conversation.
        direction: Restrict to inbound/outbound.
        message_type: Restrict to a Meta type.
        status: Restrict to a delivery status.
        sender: Restrict to a sender identifier.
        limit: Maximum rows returned.
        offset: Rows to skip for pagination.
    """

    tenant_id: str
    conversation_id: Optional[str] = None
    direction: Optional[str] = None
    message_type: Optional[str] = None
    status: Optional[str] = None
    sender: Optional[str] = None
    limit: int = 50
    offset: int = 0


@dataclass
class EventFilter:
    """Query filter for webhook event searches.

    Attributes:
        tenant_id: Owning tenant (required for isolation).
        event_type: Restrict to one normalized type.
        processing_status: Restrict to a processing state.
        limit: Maximum rows returned.
        offset: Rows to skip for pagination.
    """

    tenant_id: str
    event_type: Optional[str] = None
    processing_status: Optional[str] = None
    limit: int = 50
    offset: int = 0


class ConversationRepository(Protocol):
    """Persist and query conversations."""

    def upsert(self, conversation: Conversation) -> Conversation:
        """Insert or update by ``(tenant_id, external_chat_id)``.

        Args:
            conversation: Conversation record.

        Returns:
            Stored record.
        """
        ...  # pragma: no cover

    def get(self, tenant_id: str, conversation_id: str) -> Optional[Conversation]:
        """Fetch one conversation within a tenant.

        Args:
            tenant_id: Owning tenant.
            conversation_id: Local identifier.

        Returns:
            Record or None.
        """
        ...  # pragma: no cover

    def list(self, tenant_id: str, limit: int = 50, offset: int = 0) -> list[Conversation]:
        """List conversations for a tenant, newest activity first.

        Args:
            tenant_id: Owning tenant.
            limit: Maximum rows.
            offset: Rows to skip.

        Returns:
            Matching records.
        """
        ...  # pragma: no cover


class MessageRepository(Protocol):
    """Persist and query messages with idempotent writes."""

    def save(self, message: Message) -> Message:
        """Insert a message; duplicate idempotency keys return the original.

        Args:
            message: Message record.

        Returns:
            Stored (or previously stored) record.
        """
        ...  # pragma: no cover

    def get(self, tenant_id: str, message_id: str) -> Optional[Message]:
        """Fetch one message within a tenant.

        Args:
            tenant_id: Owning tenant.
            message_id: Local identifier.

        Returns:
            Record or None.
        """
        ...  # pragma: no cover

    def search(self, query: MessageFilter) -> list[Message]:
        """Search messages honoring tenant isolation.

        Args:
            query: Search filter.

        Returns:
            Matching records.
        """
        ...  # pragma: no cover

    def save_status(self, status: MessageStatus) -> MessageStatus:
        """Append a delivery status transition.

        Args:
            status: Status record.

        Returns:
            Stored record.
        """
        ...  # pragma: no cover

    def statuses(self, tenant_id: str, message_id: str) -> list[MessageStatus]:
        """List status transitions for a message.

        Args:
            tenant_id: Owning tenant.
            message_id: Local identifier.

        Returns:
            Status records in occurrence order.
        """
        ...  # pragma: no cover


class EventRepository(Protocol):
    """Persist webhook receipts and processing outcomes."""

    def record(self, event: WebhookEvent, raw_payload: Optional[dict] = None) -> WebhookEvent:
        """Record receipt; known hashes return the original event.

        Args:
            event: Event record.
            raw_payload: Optional encrypted raw payload when retention allows.

        Returns:
            Stored (or previously stored) record.
        """
        ...  # pragma: no cover

    def get_by_hash(self, tenant_id: str, event_hash: str) -> Optional[WebhookEvent]:
        """Fetch an event by fingerprint within a tenant.

        Args:
            tenant_id: Owning tenant.
            event_hash: Event fingerprint.

        Returns:
            Record or None.
        """
        ...  # pragma: no cover

    def search(self, query: EventFilter) -> list[WebhookEvent]:
        """Search events honoring tenant isolation.

        Args:
            query: Search filter.

        Returns:
            Matching records.
        """
        ...  # pragma: no cover

    def mark(self, event: WebhookEvent) -> WebhookEvent:
        """Persist a processing outcome.

        Args:
            event: Updated event record.

        Returns:
            Stored record.
        """
        ...  # pragma: no cover


class MediaRepository(Protocol):
    """Persist media metadata (never raw bytes by default)."""

    def save(self, media: MediaMetadata) -> MediaMetadata:
        """Store a media descriptor idempotently by external ID.

        Args:
            media: Media record.

        Returns:
            Stored (or previously stored) record.
        """
        ...  # pragma: no cover

    def get(self, tenant_id: str, media_id: str) -> Optional[MediaMetadata]:
        """Fetch a media descriptor within a tenant.

        Args:
            tenant_id: Owning tenant.
            media_id: Local identifier.

        Returns:
            Record or None.
        """
        ...  # pragma: no cover
