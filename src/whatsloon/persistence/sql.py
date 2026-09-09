"""SQLAlchemy reference implementation (``whatsloon[sql]`` extra).

Production applications may use this directly with SQLite, PostgreSQL, or
MySQL, or implement the repository protocols against another store.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any as _Any
from typing import Optional

try:
    from sqlalchemy import JSON, DateTime, String, Text, create_engine, select
    from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "SQL persistence requires the 'sql' extra: pip install 'whatsloon[sql]'."
    ) from exc

from whatsloon.persistence.base import MessageFilter
from whatsloon.persistence.models import (
    Message,
    MessageStatus,
)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base for whatsloon tables."""


class ConversationRow(Base):
    """Conversation table."""

    __tablename__ = "whatsloon_conversations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    external_chat_id: Mapped[str] = mapped_column(String(128))
    participant: Mapped[str] = mapped_column(String(128), default="")
    channel: Mapped[str] = mapped_column(String(32), default="dm")
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(32), default="active")


class MessageRow(Base):
    """Message table."""

    __tablename__ = "whatsloon_messages"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    direction: Mapped[str] = mapped_column(String(16))
    external_message_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reply_to_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    sender: Mapped[str] = mapped_column(String(128), default="")
    recipient: Mapped[str] = mapped_column(String(128), default="")
    message_type: Mapped[str] = mapped_column(String(32), default="text")
    content_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    structured_payload: Mapped[dict] = mapped_column(JSON, default=dict)
    api_version: Mapped[str] = mapped_column(String(16), default="")
    status: Mapped[str] = mapped_column(String(32), default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    correlation_id: Mapped[str] = mapped_column(String(64), default="")
    meta_trace_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), default="")


class MessageStatusRow(Base):
    """Message status table."""

    __tablename__ = "whatsloon_message_statuses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    message_id: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    external_status: Mapped[str] = mapped_column(String(32))
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class WebhookEventRow(Base):
    """Webhook event table."""

    __tablename__ = "whatsloon_webhook_events"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_hash: Mapped[str] = mapped_column(String(64), index=True)
    tenant_id: Mapped[str] = mapped_column(String(64), index=True)
    event_type: Mapped[str] = mapped_column(String(64))
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processing_status: Mapped[str] = mapped_column(String(32), default="received")
    retry_count: Mapped[int] = mapped_column(default=0)
    error_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


def create_all(url: str) -> _Any:
    """Create all whatsloon tables at a database URL.

    Args:
        url: SQLAlchemy database URL.

    Returns:
        Engine with tables created.
    """
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return engine


def _to_message(row: MessageRow) -> Message:
    """Convert a row to a domain record.

    Args:
        row: ORM row.

    Returns:
        Domain message.
    """
    return Message(
        id=row.id,
        conversation_id=row.conversation_id,
        tenant_id=row.tenant_id,
        direction=row.direction,  # type: ignore[arg-type]
        external_message_id=row.external_message_id,
        reply_to_id=row.reply_to_id,
        sender=row.sender,
        recipient=row.recipient,
        message_type=row.message_type,
        content_text=row.content_text,
        structured_payload=row.structured_payload or {},
        api_version=row.api_version,
        status=row.status,
        created_at=row.created_at,
        correlation_id=row.correlation_id,
        meta_trace_id=row.meta_trace_id,
        idempotency_key=row.idempotency_key,
    )


class SQLMessageRepository:
    """SQL-backed message repository honoring tenant isolation."""

    def __init__(self, session_factory: _Any) -> None:
        """Initialize with a session factory.

        Args:
            session_factory: Callable returning a new ORM session.
        """
        self._sessions = session_factory

    def save(self, message: Message) -> Message:
        """Insert a message; duplicate idempotency keys return the original.

        Args:
            message: Message record.

        Returns:
            Stored (or previously stored) record.
        """
        with self._sessions() as session:
            session = session
            if message.idempotency_key:
                existing = session.execute(
                    select(MessageRow).where(
                        MessageRow.tenant_id == message.tenant_id,
                        MessageRow.idempotency_key == message.idempotency_key,
                    )
                ).scalar_one_or_none()
                if existing is not None:
                    return _to_message(existing)
            session.merge(
                MessageRow(
                    id=message.id,
                    conversation_id=message.conversation_id,
                    tenant_id=message.tenant_id,
                    direction=message.direction.value,
                    external_message_id=message.external_message_id,
                    reply_to_id=message.reply_to_id,
                    sender=message.sender,
                    recipient=message.recipient,
                    message_type=message.message_type,
                    content_text=message.content_text,
                    structured_payload=message.structured_payload,
                    api_version=message.api_version,
                    status=message.status,
                    created_at=message.created_at,
                    correlation_id=message.correlation_id,
                    meta_trace_id=message.meta_trace_id,
                    idempotency_key=message.idempotency_key,
                )
            )
            session.commit()
            return message

    def get(self, tenant_id: str, message_id: str) -> Optional[Message]:
        """Fetch one message within a tenant.

        Args:
            tenant_id: Owning tenant.
            message_id: Local identifier.

        Returns:
            Record or None.
        """
        with self._sessions() as session:
            row = session.execute(
                select(MessageRow).where(
                    MessageRow.tenant_id == tenant_id, MessageRow.id == message_id
                )
            ).scalar_one_or_none()
            return _to_message(row) if row else None

    def search(self, query: MessageFilter) -> list[Message]:
        """Search messages honoring tenant isolation.

        Args:
            query: Search filter.

        Returns:
            Matching records newest first.
        """
        with self._sessions() as session:
            stmt = (
                select(MessageRow)
                .where(MessageRow.tenant_id == query.tenant_id)
                .order_by(MessageRow.created_at.desc())
                .limit(query.limit)
                .offset(query.offset)
            )
            if query.conversation_id:
                stmt = stmt.where(MessageRow.conversation_id == query.conversation_id)
            if query.direction:
                stmt = stmt.where(MessageRow.direction == query.direction)
            if query.message_type:
                stmt = stmt.where(MessageRow.message_type == query.message_type)
            if query.status:
                stmt = stmt.where(MessageRow.status == query.status)
            if query.content_contains:
                stmt = stmt.where(MessageRow.content_text.ilike(f"%{query.content_contains}%"))
            if query.since:
                stmt = stmt.where(MessageRow.created_at >= query.since)
            if query.until:
                stmt = stmt.where(MessageRow.created_at < query.until)
            return [_to_message(row) for row in session.execute(stmt).scalars()]

    def save_status(self, status: MessageStatus) -> MessageStatus:
        """Append a delivery status transition.

        Args:
            status: Status record.

        Returns:
            Stored record.
        """
        with self._sessions() as session:
            session.merge(
                MessageStatusRow(
                    id=status.id,
                    message_id=status.message_id,
                    tenant_id=status.tenant_id,
                    external_status=status.external_status,
                    error_message=status.error_message,
                    occurred_at=status.occurred_at,
                )
            )
            row = session.execute(
                select(MessageRow).where(
                    MessageRow.tenant_id == status.tenant_id,
                    MessageRow.id == status.message_id,
                )
            ).scalar_one_or_none()
            if row is not None:
                row.status = status.external_status
            session.commit()
            return status

    def statuses(self, tenant_id: str, message_id: str) -> list[MessageStatus]:
        """List status transitions for a message.

        Args:
            tenant_id: Owning tenant.
            message_id: Local identifier.

        Returns:
            Status records in occurrence order.
        """
        with self._sessions() as session:
            message = session.execute(
                select(MessageRow).where(
                    MessageRow.tenant_id == tenant_id, MessageRow.id == message_id
                )
            ).scalar_one_or_none()
            if message is None:
                return []
            rows = session.execute(
                select(MessageStatusRow)
                .where(MessageStatusRow.message_id == message_id)
                .order_by(MessageStatusRow.occurred_at)
            ).scalars()
            return [
                MessageStatus(
                    id=row.id,
                    message_id=row.message_id,
                    tenant_id=row.tenant_id,
                    external_status=row.external_status,
                    error_message=row.error_message,
                    occurred_at=row.occurred_at,
                )
                for row in rows
            ]


def session_factory(url: str) -> _Any:
    """Build a session factory for a database URL.

    Args:
        url: SQLAlchemy database URL.

    Returns:
        Session factory.
    """
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, class_=Session, expire_on_commit=False)


__all__ = [
    "Base",
    "ConversationRow",
    "MessageRow",
    "MessageStatusRow",
    "SQLMessageRepository",
    "WebhookEventRow",
    "create_all",
    "session_factory",
]
