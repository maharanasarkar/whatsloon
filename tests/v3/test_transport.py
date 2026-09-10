"""Transport behavior tests with mocked HTTP."""

import httpx
import pytest

from whatsloon.config.settings import RetryConfig, TimeoutConfig
from whatsloon.exceptions import ConnectError, ValidationAPIError
from whatsloon.transport.base import redact_headers
from whatsloon.transport.request import Request
from whatsloon.transport.sync import SyncTransport


def _transport(monkeypatch, handler, **overrides):
    """Build a SyncTransport whose httpx client is mocked."""
    policy = RetryConfig(max_attempts=overrides.pop("max_attempts", 1), jitter=False)
    transport = SyncTransport(
        base_url="https://graph.facebook.com/v26.0",
        access_token="secret",
        timeout=TimeoutConfig(),
        retry=policy,
    )

    def fake_request(self, method, url, **kwargs):
        return handler(method, url, kwargs.get("json"))

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    return transport


def _ok_response(data, status=200):
    """Build a minimal httpx response double."""
    request = httpx.Request("POST", "https://graph.facebook.com/v26.0/x")
    return httpx.Response(status, json=data, request=request)


def test_success_returns_normalized_response(monkeypatch):
    """200 responses normalize into typed Response objects."""
    transport = _transport(monkeypatch, lambda m, u, j: _ok_response({"messages": [{"id": "w-1"}]}))
    response = transport.send(Request(method="POST", path="/x/messages", json_body={"to": "1"}))
    assert response.status_code == 200
    assert response.data["messages"][0]["id"] == "w-1"
    assert response.correlation_id


def test_retry_on_server_error_then_success(monkeypatch):
    """5xx is retried; success on the second attempt wins."""
    calls = {"n": 0}

    def handler(method, url, json):
        calls["n"] += 1
        if calls["n"] == 1:
            return _ok_response({"error": {"message": "boom"}}, status=500)
        return _ok_response({"messages": [{"id": "w-2"}]})

    transport = _transport(monkeypatch, handler, max_attempts=2)
    response = transport.send(Request(method="POST", path="/x", json_body={}))
    assert response.data["messages"][0]["id"] == "w-2"
    assert calls["n"] == 2


def test_no_retry_on_validation_error(monkeypatch):
    """400 raises immediately without a second attempt."""
    calls = {"n": 0}

    def handler(method, url, json):
        calls["n"] += 1
        return _ok_response({"error": {"message": "bad"}}, status=400)

    transport = _transport(monkeypatch, handler, max_attempts=3)
    with pytest.raises(ValidationAPIError):
        transport.send(Request(method="POST", path="/x", json_body={}))
    assert calls["n"] == 1


def test_connection_failure_maps_to_typed_error(monkeypatch):
    """httpx connection failures become ConnectError."""

    def handler(method, url, json):
        raise httpx.ConnectError("dns down")

    transport = _transport(monkeypatch, handler)
    with pytest.raises(ConnectError):
        transport.send(Request(method="POST", path="/x", json_body={}))


def test_headers_redacted_for_logging():
    """Authorization headers never appear in log records."""
    assert redact_headers({"Authorization": "Bearer secret"}) == {"Authorization": "Bearer ***"}


class _Recorder:
    """Test middleware recording hook invocations."""

    def __init__(self) -> None:
        """Initialize empty records."""
        self.before: list[str] = []
        self.after: list[int] = []
        self.errors: list[str] = []

    def before_send(self, request) -> None:
        """Record a before hook.

        Args:
            request: Outbound request.
        """
        self.before.append(request.correlation_id)

    def after_send(self, request, response) -> None:
        """Record an after hook.

        Args:
            request: Outbound request.
            response: Normalized response.
        """
        self.after.append(response.status_code)

    def record_error(self, request, error) -> None:
        """Record an error hook.

        Args:
            request: Outbound request.
            error: The failure.
        """
        self.errors.append(type(error).__name__)


def test_middleware_called_per_attempt(monkeypatch):
    """Middleware observes every attempt including retries."""
    calls = {"n": 0}

    def handler(method, url, json):
        calls["n"] += 1
        if calls["n"] == 1:
            return _ok_response({"error": {"message": "boom"}}, status=500)
        return _ok_response({"messages": [{"id": "w-2"}]})

    recorder = _Recorder()
    transport = _transport(monkeypatch, handler, max_attempts=2)
    transport.middleware.append(recorder)
    transport.send(Request(method="POST", path="/x", json_body={}))
    assert len(recorder.before) == 2
    assert recorder.after == [500, 200]


def test_middleware_record_error_on_transport_failure(monkeypatch):
    """Transport failures reach record_error hooks."""

    def handler(method, url, json):
        raise httpx.ConnectError("dns down")

    recorder = _Recorder()
    transport = _transport(monkeypatch, handler)
    transport.middleware.append(recorder)
    with pytest.raises(ConnectError):
        transport.send(Request(method="POST", path="/x", json_body={}))
    assert recorder.errors == ["ConnectError"]
    assert recorder.after == []


def test_idempotency_key_sent_on_posts(monkeypatch):
    """POSTs carry the request idempotency key; GETs do not."""
    seen = {}

    def fake_request(self, method, url, **kwargs):
        seen[method] = kwargs["headers"]
        return _ok_response({})

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    transport = SyncTransport(
        base_url="https://graph.facebook.com/v26.0",
        access_token="secret",
        timeout=TimeoutConfig(),
        retry=RetryConfig(max_attempts=1, jitter=False),
    )
    request = Request(method="POST", path="/x", json_body={})
    transport.send(request)
    assert seen["POST"]["Idempotency-Key"] == request.idempotency_key
    transport.send(Request(method="GET", path="/x"))
    assert "Idempotency-Key" not in seen["GET"]


def test_concurrent_first_send_creates_one_client(monkeypatch):
    """Concurrent first sends share a single pooled client."""
    import threading

    created = []

    real_client = httpx.Client

    def counting_client(*args, **kwargs):
        created.append(1)
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", counting_client)
    transport = SyncTransport(
        base_url="https://graph.facebook.com/v26.0",
        access_token="secret",
        timeout=TimeoutConfig(),
        retry=RetryConfig(max_attempts=1, jitter=False),
    )
    threads = [threading.Thread(target=lambda: transport.client) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(created) == 1
    transport.close()
