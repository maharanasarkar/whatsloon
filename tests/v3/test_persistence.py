"""Persistence behavior tests: dedupe, isolation, retention."""

from datetime import timedelta

from whatsloon.persistence.base import EventFilter, MessageFilter
from whatsloon.persistence.models import (
    Conversation,
    Direction,
    Message,
    MessageStatus,
    ProcessingStatus,
    WebhookEvent,
    utcnow,
)
from whatsloon.persistence.policies import RetentionPolicy, fingerprint
from whatsloon.persistence.repositories import (
    InMemoryConversationRepository,
    InMemoryEventRepository,
    InMemoryMessageRepository,
)


def _message(**overrides):
    """Build a message record with sane defaults.

    Args:
        **overrides: Field overrides.

    Returns:
        Message record.
    """
    values = {
        "id": "m-1",
        "conversation_id": "c-1",
        "tenant_id": "t-1",
        "direction": Direction.OUTBOUND,
        "sender": "919876543210",
        "recipient": "919000000001",
        "content_text": "Hello",
        "idempotency_key": "key-1",
    }
    values.update(overrides)
    return Message(**values)


def test_idempotent_save_returns_original():
    """Duplicate idempotency keys never create a second row."""
    repos = InMemoryMessageRepository()
    first = repos.save(_message())
    second = repos.save(_message(id="m-2", content_text="changed"))
    assert second.id == first.id == "m-1"
    assert second.content_text == "Hello"


def test_tenant_isolation_on_read_and_search():
    """Tenants cannot see each other's messages."""
    repos = InMemoryMessageRepository()
    repos.save(_message())
    assert repos.get("t-2", "m-1") is None
    assert repos.search(MessageFilter(tenant_id="t-2")) == []


def test_status_transitions_update_message():
    """Status writes append history and roll up the latest state."""
    repos = InMemoryMessageRepository()
    repos.save(_message())
    repos.save_status(
        MessageStatus(id="s-1", message_id="m-1", tenant_id="t-1", external_status="delivered")
    )
    assert repos.get("t-1", "m-1").status == "delivered"
    assert [s.external_status for s in repos.statuses("t-1", "m-1")] == ["delivered"]
    assert repos.statuses("t-2", "m-1") == []


def test_event_hash_dedupe():
    """Duplicate webhook deliveries collapse to one event."""
    repos = InMemoryEventRepository()
    event = WebhookEvent(id="e-1", event_hash="h-1", tenant_id="t-1", event_type="message.received")
    assert repos.record(event).id == "e-1"
    assert repos.record(event.model_copy(update={"id": "e-2"})).id == "e-1"
    assert repos.get_by_hash("t-1", "h-1").id == "e-1"
    assert repos.get_by_hash("t-2", "h-1") is None


def test_conversation_upsert_and_order():
    """Upserts merge on external chat; listing is newest-first."""
    repos = InMemoryConversationRepository()
    repos.upsert(Conversation(id="c-1", tenant_id="t-1", external_chat_id="chat-1"))
    merged = repos.upsert(
        Conversation(id="c-9", tenant_id="t-1", external_chat_id="chat-1", participant="919")
    )
    assert merged.id == "c-1"
    assert repos.get("t-1", "c-1").participant == "919"
    assert repos.get("t-2", "c-1") is None


def test_retention_expiry_and_anonymization():
    """Retention flags expired records and strips PII on request."""
    policy = RetentionPolicy(retention_days=30)
    message = _message()
    message.retention_expires_at = policy.expires_at(message.created_at)
    assert policy.is_expired(message, now=message.created_at + timedelta(days=31)) is True
    assert policy.is_expired(message, now=message.created_at) is False
    clean = policy.anonymize(message)
    assert clean.sender == "redacted" and clean.content_text is None
    assert message.sender == "919876543210"


def test_fingerprint_is_stable():
    """Fingerprints ignore key order for dedupe."""
    assert fingerprint({"b": 1, "a": 2}) == fingerprint({"a": 2, "b": 1})
    assert len(fingerprint({"a": 1})) == 64


def test_content_and_time_filters():
    """Substring and time bounds narrow message searches."""
    repos = InMemoryMessageRepository()
    base = utcnow()
    repos.save(_message(id="m-1", content_text="Hello world", created_at=base))
    repos.save(
        _message(
            id="m-2",
            content_text="Goodbye",
            created_at=base + timedelta(hours=2),
            idempotency_key="key-2",
        )
    )
    assert [
        m.id for m in repos.search(MessageFilter(tenant_id="t-1", content_contains="hello"))
    ] == ["m-1"]
    assert [
        m.id for m in repos.search(MessageFilter(tenant_id="t-1", since=base + timedelta(hours=1)))
    ] == ["m-2"]
    assert (
        repos.search(
            MessageFilter(
                tenant_id="t-1",
                since=base + timedelta(hours=1),
                until=base + timedelta(hours=1),
            )
        )
        == []
    )


def test_event_time_filters():
    """Time bounds narrow event searches."""
    repos = InMemoryEventRepository()
    base = utcnow()
    repos.record(
        WebhookEvent(
            id="e-1",
            event_hash="h-1",
            tenant_id="t-1",
            event_type="message.received",
            received_at=base,
        )
    )
    repos.record(
        WebhookEvent(
            id="e-2",
            event_hash="h-2",
            tenant_id="t-1",
            event_type="message.received",
            received_at=base + timedelta(hours=2),
        )
    )
    assert [
        e.id for e in repos.search(EventFilter(tenant_id="t-1", until=base + timedelta(hours=1)))
    ] == ["e-1"]
