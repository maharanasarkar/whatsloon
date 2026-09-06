"""Admin console tests: auth, isolation, masking, raw privilege."""

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from whatsloon.admin.app import RepositoryBundle, create_app
from whatsloon.admin.auth import AdminUser, StaticTokenAuth, mask_phone, redact_payload
from whatsloon.persistence.models import Conversation, Direction, Message
from whatsloon.persistence.repositories import (
    InMemoryConversationRepository,
    InMemoryEventRepository,
    InMemoryMessageRepository,
)


def _store():
    """Build a seeded repository bundle.

    Returns:
        Seeded bundle with one tenant's conversation and message.
    """
    conversations = InMemoryConversationRepository()
    messages = InMemoryMessageRepository()
    events = InMemoryEventRepository()
    conversations.upsert(
        Conversation(
            id="c-1", tenant_id="t-1", external_chat_id="chat-1", participant="919876543210"
        )
    )
    messages.save(
        Message(
            id="m-1",
            conversation_id="c-1",
            tenant_id="t-1",
            direction=Direction.OUTBOUND,
            sender="919876543210",
            recipient="919000000001",
            content_text="Secret hello world, this is long",
            structured_payload={"access_token": "xxx", "text": "hi"},
        )
    )
    return RepositoryBundle(conversations=conversations, messages=messages, events=events)


def _client(**tokens):
    """Build an admin test client.

    Args:
        **tokens: Token to principal mapping overrides.

    Returns:
        Test client.
    """
    mapping = {
        "owner-token": AdminUser(username="owner", tenant_id="*", roles=["owner"]),
        "viewer-token": AdminUser(username="viewer", tenant_id="t-1", roles=["viewer"]),
        "other-token": AdminUser(username="other", tenant_id="t-2", roles=["viewer"]),
    }
    mapping.update(tokens)
    return TestClient(create_app(_store(), StaticTokenAuth(mapping)))


def _auth(token):
    """Build an authorization header.

    Args:
        token: Bearer token.

    Returns:
        Header mapping.
    """
    return {"Authorization": f"Bearer {token}"}


def test_unauthorized_without_token():
    """Missing credentials are rejected."""
    assert _client().get("/dashboard", params={"tenant_id": "t-1"}).status_code == 401


def test_tenant_isolation_enforced():
    """Principals cannot read outside their tenant scope."""
    client = _client()
    assert (
        client.get(
            "/messages", params={"tenant_id": "t-1"}, headers=_auth("viewer-token")
        ).status_code
        == 200
    )
    denied = client.get("/messages", params={"tenant_id": "t-1"}, headers=_auth("other-token"))
    assert denied.status_code == 403


def test_pii_masked_in_list_views():
    """List views mask identifiers and truncate content."""
    items = (
        _client()
        .get("/messages", params={"tenant_id": "t-1"}, headers=_auth("viewer-token"))
        .json()["items"]
    )
    assert items[0]["sender"] == mask_phone("919876543210") != "919876543210"
    assert "structured_payload" not in items[0]


def test_raw_payload_requires_privileged_role():
    """Raw payloads need owner/operator plus explicit flag."""
    client = _client()
    forbidden = client.get(
        "/messages/m-1",
        params={"tenant_id": "t-1", "reveal_raw": True},
        headers=_auth("viewer-token"),
    )
    assert forbidden.status_code == 403
    raw = client.get(
        "/messages/m-1",
        params={"tenant_id": "t-1", "reveal_raw": True},
        headers=_auth("owner-token"),
    ).json()
    assert raw["structured_payload"]["access_token"] == "***"
    assert raw["structured_payload"]["text"] == "hi"


def test_dashboard_counts_and_health():
    """Dashboard aggregates and health stays public."""
    client = _client()
    assert client.get("/health").json() == {"status": "ok"}
    body = client.get(
        "/dashboard", params={"tenant_id": "t-1"}, headers=_auth("owner-token")
    ).json()
    assert body["outbound"] == 1 and body["tenant_id"] == "t-1"


def test_no_auth_backend_refused():
    """Creating the app without auth raises instead of serving open."""
    with pytest.raises(RuntimeError):
        create_app(_store(), None)


def test_redact_payload_nested():
    """Secret keys are redacted at any depth."""
    assert redact_payload({"a": {"access_token": "x"}, "b": [1]}) == {
        "a": {"access_token": "***"},
        "b": [1],
    }
