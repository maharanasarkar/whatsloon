"""Context client tests with stubbed transports."""

import pytest

from whatsloon.async_client import AsyncWhatsApp
from whatsloon.client import WhatsApp, normalize_recipient
from whatsloon.config.settings import RetryConfig, TimeoutConfig
from whatsloon.exceptions import ConfigurationError, ValidationError
from whatsloon.transport.request import Request
from whatsloon.transport.response import Response
from whatsloon.transport.sync import SyncTransport


class FakeSyncTransport(SyncTransport):
    """In-memory transport returning canned responses."""

    def __init__(self, payload):
        """Initialize with a canned Meta payload.

        Args:
            payload: Decoded body returned for every request.
        """
        super().__init__(
            base_url="https://graph.facebook.com/v26.0",
            access_token="test",
            timeout=TimeoutConfig(),
            retry=RetryConfig(max_attempts=1),
        )
        self.payload = payload
        self.seen = []

    def send(self, request):
        """Record and answer with the canned payload.

        Args:
            request: Outbound request.

        Returns:
            Normalized canned response.
        """
        self.seen.append(request)
        return Response(status_code=200, data=self.payload, correlation_id=request.correlation_id)


def _client(payload=None, **kwargs):
    """Build a client over a fake transport.

    Args:
        payload: Canned Meta body.
        **kwargs: Forwarded to :class:`WhatsApp`.

    Returns:
        Tuple of client and fake transport.
    """
    fake = FakeSyncTransport(payload or {"messages": [{"id": "wamid.test-1"}]})
    kwargs.setdefault("access_token", "token")
    kwargs.setdefault("phone_number_id", "123")
    return WhatsApp(transport=fake, **kwargs), fake


def test_send_text_uses_adapter_and_returns_typed_result():
    """Sync send flows through adapter serialization into typed results."""
    client, fake = _client()
    result = client.send_text(to="+91 98765 43210", body="Hello!")
    assert result.message_id == "wamid.test-1"
    assert result.to == "919876543210"
    assert result.api_version == "v26.0"
    sent = fake.seen[0]
    assert sent.path == "/123/messages"
    assert sent.json_body["text"]["body"] == "Hello!"


def test_send_text_validation_before_http():
    """Invalid input raises before any transport call."""
    client, fake = _client()
    with pytest.raises(ValidationError):
        client.send_text(to="not-a-number!!!", body="Hi")
    with pytest.raises(ValidationError):
        client.send_text(to="919876543210", body="   ")
    assert fake.seen == []


def test_version_pinning_and_latest_alias():
    """Explicit pins stick; latest resolves to the pin."""
    client, _ = _client(graph_api_version="v19.0")
    assert client.version.value == "v19.0"
    assert client.adapter.api_version == "v19.0"
    pinned = WhatsApp(access_token="t", phone_number_id="123", graph_api_version="v19.0")
    try:
        assert pinned.transport.base_url.endswith("/v19.0")
    finally:
        pinned.close()
    latest, _ = _client()
    assert latest.version.value == "v26.0"
    with pytest.raises(ConfigurationError):
        _client(graph_api_version="v99.0")


def test_repr_redacts_token():
    """Client reprs never include the access token."""
    client, _ = _client(access_token="super-secret")
    assert "super-secret" not in repr(client)
    assert "super-secret" not in repr(client.config)


def test_graph_escape_hatch_posts_raw_path():
    """Raw graph access reaches the transport untouched."""
    client, fake = _client()
    response = client.graph.post(path="/123/custom", json={"a": 1})
    assert response.status_code == 200
    assert fake.seen[0].path == "/123/custom"


def test_normalize_recipient():
    """Recipient normalization strips formatting."""
    assert normalize_recipient("+91 98765 43210") == "919876543210"


async def test_async_send_text_shares_domain_behavior():
    """Async client serializes identically to sync through shared builders."""
    from whatsloon.transport.async_ import AsyncTransport

    seen = []

    class FakeAsync(AsyncTransport):
        async def asend(self, request):
            seen.append(request)
            return Response(
                status_code=200,
                data={"messages": [{"id": "wamid.async-1"}]},
                correlation_id=request.correlation_id,
            )

    wa = AsyncWhatsApp(access_token="t", phone_number_id="123")
    wa.transport = FakeAsync(
        base_url="https://graph.facebook.com/v26.0",
        access_token="t",
        timeout=TimeoutConfig(),
        retry=RetryConfig(max_attempts=1),
    )
    async with wa.transport:
        wa.graph.transport = wa.transport
        result = await wa.send_text(to="919876543210", body="Hello async!")
    assert result.message_id == "wamid.async-1"
    assert seen[0].json_body["text"]["body"] == "Hello async!"


def test_compat_shim_warns_and_reexports():
    """Legacy entry points resolve through compat with a warning."""
    import warnings

    import whatsloon.compat as compat

    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cls = compat.WhatsAppCloudAPIClient
    assert cls.__name__ == "WhatsAppCloudAPIClient"
    assert any(issubclass(w.category, DeprecationWarning) for w in caught)
