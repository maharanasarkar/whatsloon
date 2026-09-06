"""Template and business service tests with mocked HTTP."""

import httpx

from whatsloon.business.service import BusinessService
from whatsloon.config.settings import RetryConfig, TimeoutConfig
from whatsloon.templates.models import TemplateSpec
from whatsloon.templates.service import TemplateService
from whatsloon.transport.response import Response
from whatsloon.transport.sync import SyncTransport


def _transport(monkeypatch, routes):
    """Build a transport dispatching canned responses by path.

    Args:
        monkeypatch: Pytest fixture.
        routes: Mapping of (method, path) to JSON body.

    Returns:
        Tuple of transport and captured calls.
    """
    calls = []
    transport = SyncTransport(
        base_url="https://graph.facebook.com/v26.0",
        access_token="secret",
        timeout=TimeoutConfig(),
        retry=RetryConfig(max_attempts=1, jitter=False),
    )

    def fake_request(self, method, url, **kwargs):
        calls.append((method, url, kwargs))
        path = url.replace("https://graph.facebook.com/v26.0", "")
        body = routes.get((method, path), {})
        request = httpx.Request(method, url)
        return httpx.Response(200, json=body, request=request)

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    return transport, calls


def test_template_lifecycle(monkeypatch):
    """Template list/create/delete hit versioned Manager paths."""
    routes = {
        ("GET", "/waba-1/message_templates"): {
            "data": [{"id": "t-1", "name": "hello", "status": "APPROVED"}]
        },
        ("POST", "/waba-1/message_templates"): {"id": "t-2"},
        ("DELETE", "/waba-1/message_templates"): {"success": True},
    }
    transport, calls = _transport(monkeypatch, routes)
    service = TemplateService(transport)
    listed = service.list_templates("waba-1")
    assert [t.name for t in listed] == ["hello"]
    created = service.create_template(
        "waba-1", TemplateSpec(name="new", language="en_US", category="UTILITY")
    )
    assert created.id == "t-2" and created.name == "new"
    assert service.delete_template("waba-1", "hello") is True
    assert [c[0] for c in calls] == ["GET", "POST", "DELETE"]
    assert calls[2][2]["params"] == {"name": "hello"}
    assert calls[1][2]["json"]["category"] == "UTILITY"


def test_business_reads_and_registration(monkeypatch):
    """WABA reads and phone registration follow Manager contracts."""
    routes = {
        ("GET", "/waba-1"): {"id": "waba-1", "name": "Acme"},
        ("GET", "/waba-1/phone_numbers"): {
            "data": [{"id": "123", "display_phone_number": "+919000000000"}]
        },
        ("GET", "/123"): {"id": "123", "quality_rating": "GREEN"},
        ("POST", "/123/register"): {"success": True},
        ("POST", "/123/deregister"): {"success": True},
    }
    transport, calls = _transport(monkeypatch, routes)
    service = BusinessService(transport)
    assert service.get_account("waba-1").name == "Acme"
    assert service.list_phone_numbers("waba-1")[0].id == "123"
    assert service.get_phone_number("123").quality_rating == "GREEN"
    assert service.register_phone("123", pin="123456") is True
    assert service.deregister_phone("123") is True
    register = [c for c in calls if c[1].endswith("/register")][0]
    assert register[2]["json"] == {"messaging_product": "whatsapp", "pin": "123456"}


def test_services_wired_on_clients():
    """Clients expose templates and business services."""
    from whatsloon.client import WhatsApp

    client = WhatsApp(access_token="t", phone_number_id="123")
    try:
        assert isinstance(client.templates, TemplateService)
        assert isinstance(client.business, BusinessService)
    finally:
        client.close()
