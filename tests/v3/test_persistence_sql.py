"""SQL reference repository tests on SQLite."""

import pytest

sqlalchemy = pytest.importorskip("sqlalchemy")

from whatsloon.persistence.base import MessageFilter
from whatsloon.persistence.models import Direction, Message, MessageStatus
from whatsloon.persistence.sql import SQLMessageRepository, session_factory


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
        "content_text": "Hello SQL",
        "idempotency_key": "sql-key-1",
    }
    values.update(overrides)
    return Message(**values)


def test_sql_save_search_status_roundtrip(tmp_path):
    """SQL repos persist, isolate tenants, and track statuses."""
    factory = session_factory(f"sqlite:///{tmp_path}/admin.db")
    repos = SQLMessageRepository(factory)
    repos.save(_message())
    assert repos.get("t-1", "m-1").content_text == "Hello SQL"
    assert repos.get("t-2", "m-1") is None
    assert len(repos.search(MessageFilter(tenant_id="t-1"))) == 1
    repos.save_status(
        MessageStatus(id="s-1", message_id="m-1", tenant_id="t-1", external_status="read")
    )
    assert repos.get("t-1", "m-1").status == "read"
    assert [s.external_status for s in repos.statuses("t-1", "m-1")] == ["read"]


def test_sql_idempotent_save(tmp_path):
    """Duplicate idempotency keys return the original SQL row."""
    factory = session_factory(f"sqlite:///{tmp_path}/admin.db")
    repos = SQLMessageRepository(factory)
    repos.save(_message())
    second = repos.save(_message(id="m-2", content_text="changed"))
    assert second.id == "m-1"
