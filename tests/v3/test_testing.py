"""Testing fakes: scripted clients and mock Meta servers."""

import pytest

from whatsloon.client import WhatsApp
from whatsloon.exceptions import RateLimitError, WhatsAppError
from whatsloon.messages.models import OutboundMessage, TextMessage
from whatsloon.testing.fakes import FakeTransport, MockMetaServer, make_fake_client


def test_fake_client_runs_real_stack():
    """Scripted clients serialize through adapters and return typed results."""
    client, fake = make_fake_client([{"messages": [{"id": "wamid.fake-1"}]}])
    result = client.messages.send_text(to="919876543210", body="Hi")
    assert result.message_id == "wamid.fake-1"
    assert fake.seen[0].json_body["text"]["body"] == "Hi"
    client.close()


def test_fake_transport_replays_errors_and_exhaustion():
    """Scripted exceptions surface; exhausted scripts fail loudly."""
    client, _ = make_fake_client([RateLimitError("Slow.", retry_after=1.0)])
    with pytest.raises(RateLimitError):
        client.messages.send_text(to="919876543210", body="Hi")
    with pytest.raises(AssertionError):
        client.messages.send_text(to="919876543210", body="Hi")
    client.close()


def test_mock_server_serves_routes_and_errors():
    """Mock servers answer known routes and Meta-style errors otherwise."""
    server = MockMetaServer()
    client = WhatsApp(access_token="t", phone_number_id="123", transport=server.transport())
    try:
        result = client.messages.send(
            OutboundMessage(to="919876543210", content=TextMessage(body="Hi"))
        )
        assert result.message_id == "wamid.mock-1"
        upload = client.media.upload_bytes(b"bytes", "image/jpeg", filename="a.jpg")
        assert upload.media_id == "mock-media-1"
        with pytest.raises(WhatsAppError):
            client.graph.get(path="/unknown-route")
        assert len(server.requests) == 3
    finally:
        client.close()
