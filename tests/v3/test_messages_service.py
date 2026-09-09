"""Message service tests over stubbed transports."""

from whatsloon.async_client import AsyncWhatsApp
from whatsloon.client import WhatsApp
from whatsloon.config.settings import RetryConfig, TimeoutConfig
from whatsloon.messages.models import ListMessage, OutboundMessage, TextMessage
from whatsloon.transport.async_ import AsyncTransport
from whatsloon.transport.response import Response
from whatsloon.transport.sync import SyncTransport


class FakeSyncTransport(SyncTransport):
    """In-memory sync transport returning canned responses."""

    def __init__(self, payload=None):
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
        self.payload = payload or {"messages": [{"id": "wamid.svc-1"}]}
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


def _client(**kwargs):
    """Build a sync client over a fake transport.

    Args:
        **kwargs: Forwarded to :class:`WhatsApp`.

    Returns:
        Tuple of client and fake transport.
    """
    fake = FakeSyncTransport()
    kwargs.setdefault("access_token", "token")
    kwargs.setdefault("phone_number_id", "123")
    return WhatsApp(transport=fake, **kwargs), fake


def test_generic_send_envelope():
    """Generic envelope send serializes typed content."""
    client, fake = _client()
    result = client.messages.send(
        OutboundMessage(to="919876543210", content=TextMessage(body="Hi"))
    )
    assert result.message_id == "wamid.svc-1"
    assert fake.seen[0].json_body["text"]["body"] == "Hi"


def test_per_type_methods_cover_all_senders():
    """Every 2.x sender has a service equivalent."""
    client, fake = _client()
    client.messages.send_text(to="919876543210", body="Hi")
    client.messages.send_image(to="919876543210", media_id="m")
    client.messages.send_video(to="919876543210", media_link="https://x/v.mp4")
    client.messages.send_audio(to="919876543210", media_id="m")
    client.messages.send_document(to="919876543210", filename="a.pdf")
    client.messages.send_sticker(to="919876543210", media_id="m")
    client.messages.send_reaction(to="919876543210", message_id="w-1", emoji="👍")
    client.messages.send_location(to="919876543210", latitude=1.0, longitude=2.0)
    client.messages.send_contacts(to="919876543210", contacts=[{"name": {"formatted_name": "A"}}])
    client.messages.send_template(to="919876543210", template_name="t", language_code="en_US")
    client.messages.send_list(
        to="919876543210",
        content=ListMessage(body_text="b", button_text="Menu", sections=[{"rows": []}]),
    )
    client.messages.send_location_request(to="919876543210", body_text="Share?")
    client.messages.send_typing(message_id="w-1")
    client.messages.mark_read(message_id="w-1")
    kinds = [call.json_body.get("type") for call in fake.seen]
    assert kinds == [
        "text",
        "image",
        "video",
        "audio",
        "document",
        "sticker",
        "reaction",
        "location",
        "contacts",
        "template",
        "interactive",
        "interactive",
        None,
        None,
    ]


def test_reply_to_injects_context():
    """Reply sends carry the context block."""
    client, fake = _client()
    client.messages.send_text(to="919876543210", body="Hi", reply_to="w-9")
    assert fake.seen[0].json_body["context"] == {"message_id": "w-9"}


async def test_async_service_shares_serialization():
    """Async service produces identical payloads through shared builders."""
    seen = []

    class FakeAsync(AsyncTransport):
        async def asend(self, request):
            seen.append(request)
            return Response(
                status_code=200,
                data={"messages": [{"id": "wamid.async-svc"}]},
                correlation_id=request.correlation_id,
            )

    wa = AsyncWhatsApp(access_token="t", phone_number_id="123")
    wa.transport = FakeAsync(
        base_url="https://graph.facebook.com/v26.0",
        access_token="t",
        timeout=TimeoutConfig(),
        retry=RetryConfig(max_attempts=1),
    )
    from whatsloon.messages.service import AsyncMessageService

    wa.messages = AsyncMessageService(wa.adapter, wa.transport, "123")
    async with wa.transport:
        result = await wa.messages.send_template(
            to="919876543210", template_name="t", language_code="en_US"
        )
    assert result.message_id == "wamid.async-svc"
    assert seen[0].json_body["template"]["name"] == "t"


def test_outbound_persist_records_message_and_conversation():
    """Opt-in stores persist outbound sends with linked conversations."""
    from whatsloon.messages.service import MessageService
    from whatsloon.persistence.repositories import (
        InMemoryConversationRepository,
        InMemoryMessageRepository,
    )

    fake = FakeSyncTransport()
    messages = InMemoryMessageRepository()
    conversations = InMemoryConversationRepository()
    client, _ = _client()
    service = MessageService(
        client.adapter,
        fake,
        "123",
        message_store=messages,
        conversation_store=conversations,
        tenant_id="t-1",
    )
    result = service.send_text(to="919876543210", body="Persist me")
    assert result.message_id == "wamid.svc-1"
    from whatsloon.persistence.base import MessageFilter

    stored = messages.search(MessageFilter(tenant_id="t-1"))
    assert len(stored) == 1
    assert stored[0].direction.value == "outbound"
    assert stored[0].content_text == "Persist me"
    assert stored[0].external_message_id == "wamid.svc-1"
    convos = conversations.list("t-1")
    assert len(convos) == 1
    assert stored[0].conversation_id == convos[0].id


def test_outbound_without_stores_sends_normally():
    """Stores default off; sends work without persistence."""
    from whatsloon.messages.service import MessageService

    fake = FakeSyncTransport()
    client, _ = _client()
    service = MessageService(client.adapter, fake, "123")
    assert service.send_text(to="919876543210", body="Hi").message_id == "wamid.svc-1"
