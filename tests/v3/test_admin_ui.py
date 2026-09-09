"""Admin HTML UI tests: pages, partials, auth, masking, gating."""

import pytest

fastapi = pytest.importorskip("fastapi")
pytest.importorskip("jinja2")

from fastapi.testclient import TestClient

from whatsloon.admin.app import RepositoryBundle, create_app
from whatsloon.admin.auth import AdminUser, StaticTokenAuth
from whatsloon.persistence.models import (
    Conversation,
    Direction,
    Message,
    ProcessingStatus,
    WebhookEvent,
)
from whatsloon.persistence.repositories import (
    InMemoryConversationRepository,
    InMemoryEventRepository,
    InMemoryMessageRepository,
)


def _store():
    """Build a seeded repository bundle.

    Returns:
        Seeded bundle with one tenant's records.
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
            content_text="Hello UI world",
            status="delivered",
            structured_payload={"text": "hi"},
        )
    )
    events.record(
        WebhookEvent(
            id="e-1",
            event_hash="h-1",
            tenant_id="t-1",
            event_type="message.received",
            processing_status=ProcessingStatus.FAILED,
            error_summary="boom",
        )
    )
    return RepositoryBundle(conversations=conversations, messages=messages, events=events)


def _client():
    """Build a UI test client.

    Returns:
        Test client with owner and viewer tokens.
    """
    mapping = {
        "owner-token": AdminUser(username="owner", tenant_id="*", roles=["owner"]),
        "viewer-token": AdminUser(username="viewer", tenant_id="t-1", roles=["viewer"]),
    }
    return TestClient(create_app(_store(), StaticTokenAuth(mapping)))


def _q(token, tenant="t-1"):
    """Build a query string for UI navigation.

    Args:
        token: Bearer token value.
        tenant: Tenant scope.

    Returns:
        Query string.
    """
    return f"?tenant_id={tenant}&token={token}"


def test_dashboard_renders_stats_and_masks_phones():
    """Dashboard shows counts and never raw phone numbers."""
    html = _client().get("/ui/dashboard" + _q("viewer-token")).text
    assert (
        "text/html" in _client().get("/ui/dashboard" + _q("viewer-token")).headers["content-type"]
    )
    assert "Dashboard" in html
    assert "919876543210" not in html
    assert "91••••3210" in html


def test_ui_requires_auth_and_tenant_scope():
    """Missing tokens 401; other tenants 403 with an error page."""
    client = _client()
    assert client.get("/ui/dashboard?tenant_id=t-1").status_code == 401
    denied = client.get("/ui/messages" + _q("viewer-token", "t-2"))
    assert denied.status_code == 403
    assert "role=" in denied.text and "alert" in denied.text


def test_messages_page_filters_and_detail():
    """Message list filters work; detail shows history and gating."""
    client = _client()
    page = client.get("/ui/messages" + _q("viewer-token") + "&status=delivered").text
    assert "Hello UI world" in page
    assert "aria-current" in page
    empty = client.get("/ui/messages" + _q("viewer-token") + "&status=failed").text
    assert "No messages match" in empty
    detail = client.get("/ui/messages/m-1" + _q("owner-token")).text
    assert "delivered" in detail
    assert "Reveal redacted payload" in detail
    revealed = client.get("/ui/messages/m-1" + _q("owner-token") + "&reveal_raw=true").text
    assert "hi" in revealed
    viewer_reveal = client.get("/ui/messages/m-1" + _q("viewer-token") + "&reveal_raw=true")
    assert viewer_reveal.status_code == 403
    assert client.get("/ui/messages/nope" + _q("owner-token")).status_code == 404


def test_partials_return_fragments():
    """HTMX partials return rows without the page shell."""
    client = _client()
    fragment = client.get("/ui/partials/messages" + _q("viewer-token")).text
    assert "<tr>" in fragment and "<html" not in fragment
    assert "Hello UI world" in fragment
    denied = client.get("/ui/partials/events?tenant_id=t-2&token=viewer-token")
    assert denied.status_code == 403


def test_events_page_highlights_failures():
    """Failed events render with failure styling."""
    html = _client().get("/ui/events" + _q("viewer-token")).text
    assert "message.received" in html
    assert "fail" in html


def test_css_served_without_build():
    """Bundled stylesheet serves with the correct media type."""
    response = _client().get("/ui/static/admin.css")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/css")
    assert ":root" in response.text


def test_conversations_empty_state():
    """Unknown tenants render empty states, not blank pages."""
    html = _client().get("/ui/conversations" + _q("owner-token", "nobody")).text
    assert 'role="status"' in html
