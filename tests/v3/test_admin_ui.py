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
    messages.save(
        Message(
            id="m-2",
            conversation_id="c-1",
            tenant_id="t-1",
            direction=Direction.INBOUND,
            sender="919000000001",
            recipient="919876543210",
            content_text="Reply here",
            status="read",
            structured_payload={"text": "Reply here"},
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


def test_conversation_thread_chronological_and_linked():
    """Thread pages show bubbles oldest-first with detail links."""
    client = _client()
    html = client.get("/ui/conversations/c-1" + _q("viewer-token")).text
    assert "91••••3210" in html
    assert "919876543210" not in html
    first = html.index("Hello UI world")
    second = html.index("Reply here")
    assert first < second
    assert "/ui/messages/m-1" in html
    assert client.get("/ui/conversations/nope" + _q("viewer-token")).status_code == 404
    assert client.get("/ui/conversations/c-1" + _q("viewer-token", "t-2")).status_code == 403


def test_pagination_prev_next():
    """List pages expose working prev/next navigation."""
    client = _client()
    page1 = client.get("/ui/messages" + _q("viewer-token") + "&limit=1&offset=0").text
    assert "offset=1" in page1
    assert "offset=-" not in page1
    page2 = client.get("/ui/messages" + _q("viewer-token") + "&limit=1&offset=1").text
    assert "offset=0" in page2
    assert "Hello UI world" in page2 or "Reply here" in page2


def test_content_search_and_dates():
    """Substring search and date bounds filter messages; bad dates ignored."""
    client = _client()
    assert "Reply here" in client.get("/ui/messages" + _q("viewer-token") + "&q=reply").text
    assert "No messages match" in client.get("/ui/messages" + _q("viewer-token") + "&q=zzz").text
    assert (
        "Hello UI world"
        in client.get("/ui/messages" + _q("viewer-token") + "&since=2000-01-01").text
    )
    assert (
        "No messages match"
        in client.get("/ui/messages" + _q("viewer-token") + "&since=2999-01-01").text
    )
    assert (
        "Hello UI world"
        in client.get("/ui/messages" + _q("viewer-token") + "&since=not-a-date").text
    )
    fragment = client.get("/ui/partials/messages" + _q("viewer-token") + "&q=reply").text
    assert "Reply here" in fragment and "<html" not in fragment


def _retry_client():
    """Build a UI client wired to a processor with a failed event.

    Returns:
        Test client with a retained failed event.
    """
    from whatsloon.webhooks.events import WebhookMessageReceived
    from whatsloon.webhooks.processor import WebhookProcessor
    from whatsloon.webhooks.router import EventRouter

    store = _store()
    router = EventRouter()
    router.register("message.received", lambda event: None)
    processor = WebhookProcessor(
        router=router, events=store.events, tenant_resolver=lambda e: "t-1", retain_raw=True
    )
    record = WebhookEvent(
        id="e-ui-retry",
        event_hash="h-ui-retry",
        tenant_id="t-1",
        event_type="message.received",
        processing_status=ProcessingStatus.FAILED,
        has_raw_payload=True,
    )
    store.events.record(record, WebhookMessageReceived(message_id="w-ui").model_dump())
    mapping = {"owner-token": AdminUser(username="owner", tenant_id="*", roles=["owner"])}
    return TestClient(create_app(store, StaticTokenAuth(mapping), processor=processor))


def test_retry_button_and_row_update():
    """Failed rows offer retry; posting updates the row in place."""
    client = _retry_client()
    page = client.get("/ui/events" + _q("owner-token")).text
    assert "Retry" in page
    assert "Show failed only" in page
    row = client.post("/ui/events/e-ui-retry/retry?tenant_id=t-1&token=owner-token")
    assert row.status_code == 200
    assert "processed" in row.text
    assert 'id="event-e-ui-retry"' in row.text
    assert client.post("/ui/events/nope/retry?tenant_id=t-1&token=owner-token").status_code == 404


def test_retry_hidden_without_processor():
    """Unwired consoles show no retry controls."""
    assert "Retry" not in _client().get("/ui/events" + _q("owner-token")).text


def test_login_logout_session_flow():
    """Token login sets a session cookie; logout clears it."""
    client = _client()
    form = client.get("/ui/login")
    assert form.status_code == 200
    assert 'name="api_token"' in form.text
    denied = client.post("/ui/login", data={"api_token": "nope"})
    assert denied.status_code == 401
    assert "Unknown token" in denied.text
    logged = client.post("/ui/login", data={"api_token": "viewer-token"}, follow_redirects=False)
    assert logged.status_code == 303
    assert "wa_session=" in logged.headers.get("set-cookie", "")
    assert "httponly" in logged.headers.get("set-cookie", "").lower()
    dashboard = client.get("/ui/dashboard?tenant_id=t-1")
    assert dashboard.status_code == 200
    assert "viewer" in dashboard.text
    logout = client.post("/ui/logout", follow_redirects=False)
    assert logout.status_code == 303
    assert client.get("/ui/dashboard?tenant_id=t-1").status_code == 401


def _managed_client():
    """Build a UI client wired to stubbed Meta services.

    Returns:
        Test client with canned managers.
    """
    from types import SimpleNamespace

    from whatsloon.templates.models import TemplateInfo

    templates = SimpleNamespace(
        list_templates=lambda waba_id: [
            TemplateInfo(id="t-1", name="hello", status="APPROVED", language="en_US")
        ],
        create_template=lambda waba_id, spec: TemplateInfo(id="t-2", name=spec.name),
        calls=[],
    )
    orig_create = templates.create_template

    def _create(waba_id, spec):
        templates.calls.append((waba_id, spec.name))
        return orig_create(waba_id, spec)

    templates.create_template = _create
    media = SimpleNamespace(
        upload_bytes=lambda content, mime, filename="u": SimpleNamespace(
            media_id="mid-1", filename=filename
        )
    )
    groups = SimpleNamespace(
        list_groups=lambda: [SimpleNamespace(id="g-1", subject="Team", invite_link="https://x")]
    )
    wa = SimpleNamespace(templates=templates, media=media, groups=groups)
    mapping = {
        "owner-token": AdminUser(username="owner", tenant_id="*", roles=["owner"]),
        "viewer-token": AdminUser(username="viewer", tenant_id="t-1", roles=["viewer"]),
    }
    return TestClient(create_app(_store(), StaticTokenAuth(mapping), wa=wa))


def test_managers_hidden_without_client():
    """Manager navigation hides when no client is wired."""
    assert "Templates" not in _client().get("/ui/dashboard" + _q("owner-token")).text


def test_template_list_and_create():
    """Template pages list and create through the wired client."""
    client = _managed_client()
    page = client.get("/ui/templates" + _q("owner-token") + "&waba_id=w-1").text
    assert "hello" in page
    assert "Templates" in page
    created = client.post(
        "/ui/templates/create",
        data={
            "tenant_id": "t-1",
            "token": "owner-token",
            "waba_id": "w-1",
            "name": "new_tpl",
            "language": "en_US",
            "category": "UTILITY",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303


def test_media_upload_and_groups_list():
    """Media uploads return IDs; groups list renders."""
    client = _managed_client()
    assert "Upload" in client.get("/ui/media" + _q("owner-token")).text
    uploaded = client.post(
        "/ui/media",
        data={"tenant_id": "t-1", "token": "owner-token", "mime_type": "image/jpeg"},
        files={"file": ("a.jpg", b"bytes", "image/jpeg")},
    )
    assert "mid-1" in uploaded.text
    assert "Team" in client.get("/ui/groups" + _q("owner-token")).text


def test_manager_forbidden_for_other_tenant():
    """Manager routes enforce tenant scope."""
    client = _managed_client()
    assert client.get("/ui/templates" + _q("viewer-token", "t-2")).status_code == 403
