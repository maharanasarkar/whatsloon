"""Call service tests with mocked Calling API."""

import httpx

from whatsloon.calls.models import CallAction
from whatsloon.calls.service import CallService
from whatsloon.config.settings import RetryConfig, TimeoutConfig
from whatsloon.transport.sync import SyncTransport


def _service(monkeypatch, routes):
    """Build a call service over mocked HTTP.

    Args:
        monkeypatch: Pytest fixture.
        routes: Mapping of (method, path) to JSON body.

    Returns:
        Tuple of service and captured calls.
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
        request = httpx.Request(method, url)
        key = (method, path.split("?")[0])
        return httpx.Response(200, json=routes.get(key, {"success": True}), request=request)

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    return CallService(transport, "123"), calls


def test_call_lifecycle(monkeypatch):
    """Connect/pre_accept/accept/reject/terminate hit the calls path."""
    routes = {("POST", "/123/calls"): {"calls": [{"id": "wacid.call-1"}]}}
    service, calls = _service(monkeypatch, routes)
    connected = service.connect(to="16315553602", sdp_offer="v=0\r\n")
    assert connected["calls"][0]["id"] == "wacid.call-1"
    service.pre_accept(call_id="wacid.call-1", sdp_answer="v=0\r\n")
    service.accept(call_id="wacid.call-1", sdp_answer="v=0\r\n")
    service.reject(call_id="wacid.call-1")
    service.terminate(call_id="wacid.call-1")
    assert len(calls) == 5
    connect_body = calls[0][2]["json"]
    assert connect_body["action"] == "connect"
    assert connect_body["session"]["sdp_type"] == "offer"
    accept_body = calls[2][2]["json"]
    assert accept_body["session"]["sdp_type"] == "answer"
    assert calls[4][2]["json"] == {
        "messaging_product": "whatsapp",
        "call_id": "wacid.call-1",
        "action": "terminate",
    }


def test_permissions_and_settings(monkeypatch):
    """Permission and settings reads follow versioned paths."""
    routes = {
        ("GET", "/123/call_permissions"): {"status": "granted"},
        ("GET", "/123/settings"): {"status": "enabled"},
    }
    service, calls = _service(monkeypatch, routes)
    assert service.get_permission("16315553602").status == "granted"
    assert service.get_settings().status == "enabled"
    assert calls[0][2]["params"] == {"user_wa_id": "16315553602"}


def test_action_payload_shapes():
    """Action payloads include only relevant fields."""
    payload = CallAction(action="reject", call_id="wacid.1").payload()
    assert payload == {
        "messaging_product": "whatsapp",
        "call_id": "wacid.1",
        "action": "reject",
    }
