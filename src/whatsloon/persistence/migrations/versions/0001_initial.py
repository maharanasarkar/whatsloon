"""Initial whatsloon persistence schema."""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create whatsloon tables."""
    op.create_table(
        "whatsloon_conversations",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(64), index=True),
        sa.Column("external_chat_id", sa.String(128)),
        sa.Column("participant", sa.String(128), default=""),
        sa.Column("channel", sa.String(32), default="dm"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True)),
        sa.Column("last_activity_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), default="active"),
    )
    op.create_table(
        "whatsloon_messages",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("conversation_id", sa.String(64), index=True),
        sa.Column("tenant_id", sa.String(64), index=True),
        sa.Column("direction", sa.String(16)),
        sa.Column("external_message_id", sa.String(128), nullable=True),
        sa.Column("reply_to_id", sa.String(128), nullable=True),
        sa.Column("sender", sa.String(128), default=""),
        sa.Column("recipient", sa.String(128), default=""),
        sa.Column("message_type", sa.String(32), default="text"),
        sa.Column("content_text", sa.Text, nullable=True),
        sa.Column("structured_payload", sa.JSON, default=dict),
        sa.Column("api_version", sa.String(16), default=""),
        sa.Column("status", sa.String(32), default="pending"),
        sa.Column("created_at", sa.DateTime(timezone=True)),
        sa.Column("correlation_id", sa.String(64), default=""),
        sa.Column("meta_trace_id", sa.String(128), nullable=True),
        sa.Column("idempotency_key", sa.String(64), default=""),
    )
    op.create_table(
        "whatsloon_message_statuses",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("message_id", sa.String(64), index=True),
        sa.Column("tenant_id", sa.String(64), index=True),
        sa.Column("external_status", sa.String(32)),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("occurred_at", sa.DateTime(timezone=True)),
    )
    op.create_table(
        "whatsloon_webhook_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("event_hash", sa.String(64), index=True),
        sa.Column("tenant_id", sa.String(64), index=True),
        sa.Column("event_type", sa.String(64)),
        sa.Column("received_at", sa.DateTime(timezone=True)),
        sa.Column("processing_status", sa.String(32), default="received"),
        sa.Column("retry_count", sa.Integer, default=0),
        sa.Column("error_message", sa.Text, nullable=True),
    )


def downgrade() -> None:
    """Drop whatsloon tables."""
    op.drop_table("whatsloon_webhook_events")
    op.drop_table("whatsloon_message_statuses")
    op.drop_table("whatsloon_messages")
    op.drop_table("whatsloon_conversations")
