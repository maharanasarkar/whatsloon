"""Admin read views over persisted WhatsApp activity.

All views enforce authentication, tenant scoping, and PII masking. Raw
payloads are privileged: they require an owner/operator role plus an
explicit ``reveal_raw`` flag, and are still secret-redacted.
"""

from __future__ import annotations

from typing import Any, Optional

from whatsloon.admin.auth import AdminUser, mask_phone, mask_text, redact_payload
from whatsloon.persistence.base import EventFilter, MessageFilter
from whatsloon.persistence.models import Message


def serialize_message(message: Message, *, reveal: bool = False) -> dict[str, Any]:
    """Serialize a message for admin display with masking.

    Args:
        message: Domain record.
        reveal: Whether privileged content display is allowed. Identifiers
            stay masked regardless; only truncated content is shown.

    Returns:
        Safe display mapping.
    """
    return {
        "id": message.id,
        "conversation_id": message.conversation_id,
        "tenant_id": message.tenant_id,
        "direction": message.direction.value,
        "sender": mask_phone(message.sender),
        "recipient": mask_phone(message.recipient),
        "message_type": message.message_type,
        "content_text": message.content_text if reveal else mask_text(message.content_text),
        "status": message.status,
        "api_version": message.api_version,
        "created_at": message.created_at.isoformat(),
        "correlation_id": message.correlation_id,
        "meta_trace_id": message.meta_trace_id,
    }


def dashboard(store: Any, tenant_id: str) -> dict[str, Any]:
    """Aggregate operational counts for a tenant.

    Args:
        store: Repository bundle with ``messages`` and ``events``.
        tenant_id: Tenant scope.

    Returns:
        Counts of inbound/outbound messages, failures, and recent activity.
    """
    messages = store.messages.search(MessageFilter(tenant_id=tenant_id, limit=1000))
    inbound = sum(1 for m in messages if m.direction.value == "inbound")
    outbound = sum(1 for m in messages if m.direction.value == "outbound")
    failed = sum(1 for m in messages if m.status in ("failed", "undelivered"))
    events = store.events.search(EventFilter(tenant_id=tenant_id, limit=1000))
    pending = sum(1 for e in events if e.processing_status.value in ("received", "retrying"))
    return {
        "tenant_id": tenant_id,
        "inbound": inbound,
        "outbound": outbound,
        "failed": failed,
        "pending_events": pending,
        "recent_conversations": [
            {"id": c.id, "participant": mask_phone(c.participant)}
            for c in store.conversations.list(tenant_id, limit=5)
        ],
    }


def check_access(user: Optional[AdminUser], tenant_id: str) -> Optional[dict[str, Any]]:
    """Validate authentication and tenant scope for a request.

    Args:
        user: Authenticated principal, if any.
        tenant_id: Requested tenant.

    Returns:
        Error mapping when denied, else None.
    """
    if user is None:
        return {"error": "unauthorized", "status": 401}
    if not user.may_access(tenant_id):
        return {"error": "forbidden", "status": 403}
    return None


def message_detail(
    store: Any,
    user: AdminUser,
    tenant_id: str,
    message_id: str,
    *,
    reveal_raw: bool = False,
) -> tuple[Optional[dict[str, Any]], int]:
    """Fetch a message with privileged raw access control.

    Args:
        store: Repository bundle.
        user: Authenticated principal.
        tenant_id: Tenant scope.
        message_id: Local identifier.
        reveal_raw: Whether to include the redacted structured payload.

    Returns:
        Tuple of response mapping and HTTP status.
    """
    denied = check_access(user, tenant_id)
    if denied is not None:
        return denied, denied["status"]
    message = store.messages.get(tenant_id, message_id)
    if message is None:
        return {"error": "not_found", "status": 404}, 404
    body = serialize_message(message, reveal=reveal_raw and user.can_view_raw)
    if reveal_raw:
        if not user.can_view_raw:
            return {"error": "forbidden", "status": 403}, 403
        body["structured_payload"] = redact_payload(message.structured_payload)
    body["statuses"] = [
        {"external_status": s.external_status, "occurred_at": s.occurred_at.isoformat()}
        for s in store.messages.statuses(tenant_id, message_id)
    ]
    return body, 200


__all__ = ["check_access", "dashboard", "message_detail", "serialize_message"]
