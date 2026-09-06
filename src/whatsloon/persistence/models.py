"""Persistence domain records.

Database-agnostic Pydantic models for conversations, messages, statuses, and
webhook events. Raw Meta payloads are stored only when explicitly enabled and
never contain credentials.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


def utcnow() -> datetime:
    """Return the current UTC time.

    Returns:
        Timezone-aware UTC datetime.
    """
    return datetime.now(timezone.utc)


class Direction(str, Enum):
    """Message direction."""

    INBOUND = "inbound"
    OUTBOUND = "outbound"


class ProcessingStatus(str, Enum):
    """Webhook event processing state."""

    RECEIVED = "received"
    PROCESSED = "processed"
    FAILED = "failed"
    RETRYING = "retrying"


class Conversation(BaseModel):
    """A chat thread with one participant or group.

    Attributes:
        id: Local identifier.
        tenant_id: Owning tenant.
        external_chat_id: WhatsApp chat/user identifier.
        participant: Display participant identifier (masked at read time).
        channel: Chat type such as ``"dm"`` or ``"group"``.
        first_seen_at: First activity timestamp.
        last_activity_at: Latest activity timestamp.
        status: Optional lifecycle status.
        tags: Optional labels.
    """

    id: str
    tenant_id: str
    external_chat_id: str
    participant: str = ""
    channel: str = "dm"
    first_seen_at: datetime = Field(default_factory=utcnow)
    last_activity_at: datetime = Field(default_factory=utcnow)
    status: str = "active"
    tags: list[str] = Field(default_factory=list)


class Message(BaseModel):
    """One inbound or outbound message with operational metadata.

    Attributes:
        id: Local identifier.
        conversation_id: Owning conversation.
        tenant_id: Owning tenant.
        direction: Inbound or outbound.
        external_message_id: Meta message identifier.
        reply_to_id: Parent message for replies.
        sender: Sender identifier.
        recipient: Recipient identifier.
        message_type: Meta message type such as ``"text"``.
        content_text: Nullable plain-text content.
        structured_payload: Versioned structured content.
        api_version: Graph API version used.
        status: Delivery status such as ``"sent"``.
        created_at: Local creation time.
        sent_at: Send completion time.
        received_at: Inbound receipt time.
        correlation_id: SDK correlation ID.
        meta_trace_id: Meta trace ID when available.
        retention_expires_at: Optional expiry for retention.
        idempotency_key: Dedupe key for safe retries.
    """

    id: str
    conversation_id: str
    tenant_id: str
    direction: Direction
    external_message_id: Optional[str] = None
    reply_to_id: Optional[str] = None
    sender: str = ""
    recipient: str = ""
    message_type: str = "text"
    content_text: Optional[str] = None
    structured_payload: dict[str, Any] = Field(default_factory=dict)
    api_version: str = ""
    status: str = "pending"
    created_at: datetime = Field(default_factory=utcnow)
    sent_at: Optional[datetime] = None
    received_at: Optional[datetime] = None
    correlation_id: str = ""
    meta_trace_id: Optional[str] = None
    retention_expires_at: Optional[datetime] = None
    idempotency_key: str = ""


class MessageStatus(BaseModel):
    """A delivery/read/failed transition for a message.

    Attributes:
        id: Local identifier.
        message_id: Owning message.
        tenant_id: Owning tenant.
        external_status: Meta status such as ``"delivered"``.
        error_code: Meta error code for failures.
        error_message: Redacted error summary.
        occurred_at: Event timestamp.
    """

    id: str
    message_id: str
    tenant_id: str
    external_status: str
    error_code: Optional[int] = None
    error_message: Optional[str] = None
    occurred_at: datetime = Field(default_factory=utcnow)


class WebhookEvent(BaseModel):
    """A received webhook envelope with processing outcome.

    Attributes:
        id: Local identifier.
        event_hash: Fingerprint for duplicate suppression.
        tenant_id: Owning tenant.
        event_type: Normalized type such as ``"message.received"``.
        received_at: Receipt timestamp.
        processed_at: Completion timestamp.
        processing_status: Current processing state.
        retry_count: Handler attempts so far.
        error_summary: Redacted failure summary.
        has_raw_payload: Whether an encrypted raw payload is retained.
    """

    id: str
    event_hash: str
    tenant_id: str
    event_type: str
    received_at: datetime = Field(default_factory=utcnow)
    processed_at: Optional[datetime] = None
    processing_status: ProcessingStatus = ProcessingStatus.RECEIVED
    retry_count: int = 0
    error_summary: Optional[str] = None
    has_raw_payload: bool = False


class MediaMetadata(BaseModel):
    """Stored media descriptor; raw bytes are never persisted by default.

    Attributes:
        id: Local identifier.
        tenant_id: Owning tenant.
        external_media_id: Meta media ID.
        media_type: MIME family such as ``"image"``.
        filename: Original filename when known.
        size_bytes: Size when known.
        sha256: Content hash when available.
        created_at: Record creation time.
    """

    id: str
    tenant_id: str
    external_media_id: str
    media_type: str = ""
    filename: Optional[str] = None
    size_bytes: Optional[int] = None
    sha256: Optional[str] = None
    created_at: datetime = Field(default_factory=utcnow)
