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


def _processor_client():
    """Build a client wired to a processor with retained payloads.

    Returns:
        Test client.
    """
    from whatsloon.webhooks.processor import WebhookProcessor
    from whatsloon.webhooks.router import EventRouter

    store = _store()
    router = EventRouter()
    router.register("message.received", lambda event: None)
    processor = WebhookProcessor(
        router=router, events=store.events, tenant_resolver=lambda e: "t-1", retain_raw=True
    )
    mapping = {"owner-token": AdminUser(username="owner", tenant_id="*", roles=["owner"])}
    return TestClient(create_app(store, StaticTokenAuth(mapping), processor=processor))


def test_retry_endpoint_redispatches_failed():
    """Failed events retry from retained payloads with outcomes."""
    from whatsloon.persistence.models import ProcessingStatus, WebhookEvent
    from whatsloon.webhooks.events import WebhookMessageReceived
    from whatsloon.webhooks.processor import WebhookProcessor
    from whatsloon.webhooks.router import EventRouter

    store = _store()
    router = EventRouter()
    handled = []
    router.register("message.received", handled.append)
    processor = WebhookProcessor(
        router=router, events=store.events, tenant_resolver=lambda e: "t-1", retain_raw=True
    )
    record = WebhookEvent(
        id="e-r1",
        event_hash="h-r1",
        tenant_id="t-1",
        event_type="message.received",
        processing_status=ProcessingStatus.FAILED,
        has_raw_payload=True,
    )
    raw = WebhookMessageReceived(message_id="w-r1", sender="919").model_dump()
    store.events.record(record, raw)
    mapping = {"owner-token": AdminUser(username="owner", tenant_id="*", roles=["owner"])}
    client = TestClient(create_app(store, StaticTokenAuth(mapping), processor=processor))
    response = client.post(
        "/events/e-r1/retry", params={"tenant_id": "t-1"}, headers=_auth("owner-token")
    )
    assert response.status_code == 200
    assert response.json()["outcome"] == "handled"
    assert [e.message_id for e in handled] == ["w-r1"]
    assert store.events.get("t-1", "e-r1").processing_status == ProcessingStatus.PROCESSED


def test_retry_endpoint_statuses():
    """Retry reports missing, unavailable, and unwired distinctly."""
    from whatsloon.persistence.models import ProcessingStatus, WebhookEvent

    client = _processor_client()
    headers = _auth("owner-token")
    missing = client.post("/events/nope/retry", params={"tenant_id": "t-1"}, headers=headers)
    assert missing.status_code == 404
    assert (
        _client()
        .post("/events/nope/retry", params={"tenant_id": "t-1"}, headers=headers)
        .status_code
        == 501
    )
    denied = client.post("/events/nope/retry", params={"tenant_id": "t-1"})
    assert denied.status_code == 401


def test_redact_payload_nested():
    """Secret keys are redacted at any depth."""
    assert redact_payload({"a": {"access_token": "x"}, "b": [1]}) == {
        "a": {"access_token": "***"},
        "b": [1],
    }
