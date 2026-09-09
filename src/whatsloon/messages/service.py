"""Domain message services shared by sync and async clients.

Services serialize typed envelopes through the version adapter and execute
them on the pooled transport. Sync and async variants differ only in the
transport call.
"""

from __future__ import annotations

import logging
import uuid
from typing import Any, Optional

from whatsloon.api_versions.base import VersionAdapter
from whatsloon.client import SendMessageResult, normalize_recipient, parse_send_result
from whatsloon.messages import models as m
from whatsloon.messages.serializers import (
    serialize_envelope,
    serialize_mark_read,
    serialize_typing,
)
from whatsloon.transport.async_ import AsyncTransport
from whatsloon.transport.request import Request
from whatsloon.transport.sync import SyncTransport

logger = logging.getLogger("whatsloon.messages")


def build_envelope_request(
    adapter: VersionAdapter, *, phone_number_id: str, envelope: m.OutboundMessage
) -> Request:
    """Build a transport request for an outbound envelope.

    Args:
        adapter: Version adapter for path scoping.
        phone_number_id: Sender phone number ID.
        envelope: Envelope with recipient and typed content.

    Returns:
        Transport-ready request.
    """
    payload = serialize_envelope(envelope)
    return Request(
        method="POST",
        path=adapter.messages_path(phone_number_id),
        json_body=payload,
    )


def _envelope(
    to: str, content: m.MessageContent, reply_to: Optional[str] = None
) -> m.OutboundMessage:
    """Wrap content in a normalized envelope.

    Args:
        to: Destination identifier.
        content: Typed message content.
        reply_to: Optional parent message for contextual replies.

    Returns:
        Outbound envelope.
    """
    return m.OutboundMessage(
        to=normalize_recipient(to), content=content, reply_to_message_id=reply_to
    )


def persist_outbound(
    *,
    message_store: Any,
    conversation_store: Any,
    tenant_id: str,
    phone_number_id: str,
    envelope: m.OutboundMessage,
    result: SendMessageResult,
) -> None:
    """Persist an outbound send to message stores (best-effort).

    Storage failures are logged, never raised: the send result is
    authoritative and bookkeeping must not fail a delivered message.

    Args:
        message_store: Message repository or None.
        conversation_store: Conversation repository or None.
        tenant_id: Owning tenant.
        phone_number_id: Sender phone number ID.
        envelope: Sent envelope.
        result: Typed send result.
    """
    if message_store is None:
        return
    try:
        from whatsloon.persistence.models import Conversation, Direction, Message, utcnow

        conversation_id = envelope.to
        if conversation_store is not None:
            conversation = conversation_store.upsert(
                Conversation(
                    id=uuid.uuid4().hex,
                    tenant_id=tenant_id,
                    external_chat_id=envelope.to,
                    participant=envelope.to,
                    last_activity_at=utcnow(),
                )
            )
            conversation_id = conversation.id
        content = envelope.content
        message_store.save(
            Message(
                id=uuid.uuid4().hex,
                conversation_id=conversation_id,
                tenant_id=tenant_id,
                direction=Direction.OUTBOUND,
                external_message_id=result.message_id,
                sender=phone_number_id,
                recipient=envelope.to,
                message_type=type(content).__name__.replace("Message", "").lower(),
                content_text=getattr(content, "body", None) or getattr(content, "body_text", None),
                api_version=result.api_version,
                status="sent",
                sent_at=utcnow(),
                correlation_id=result.correlation_id,
                idempotency_key=result.correlation_id,
            )
        )
    except Exception as exc:
        logger.warning("Outbound persistence failed: %s", type(exc).__name__)


class MessageService:
    """Synchronous message operations.

    Attributes:
        adapter: Version adapter for serialization.
        transport: Shared pooled transport.
        phone_number_id: Sender phone number ID.
        message_store: Optional repository receiving outbound records.
        conversation_store: Optional repository receiving conversation records.
        tenant_id: Tenant attached to persisted records.
    """

    def __init__(
        self,
        adapter: VersionAdapter,
        transport: SyncTransport,
        phone_number_id: str,
        *,
        message_store: Any = None,
        conversation_store: Any = None,
        tenant_id: str = "default",
    ) -> None:
        """Initialize the service.

        Args:
            adapter: Version adapter for serialization.
            transport: Shared pooled transport.
            phone_number_id: Sender phone number ID.
            message_store: Optional repository receiving outbound records.
            conversation_store: Optional repository receiving conversation records.
            tenant_id: Tenant attached to persisted records.
        """
        self.adapter = adapter
        self.transport = transport
        self.phone_number_id = phone_number_id
        self.message_store = message_store
        self.conversation_store = conversation_store
        self.tenant_id = tenant_id

    def send(self, envelope: m.OutboundMessage) -> SendMessageResult:
        """Send a typed envelope.

        Args:
            envelope: Outbound message.

        Returns:
            Typed result with the Meta message identifier.

        Examples:
            >>> service.send(OutboundMessage(to="919...", content=TextMessage(body="Hi")))
        """
        envelope.to = normalize_recipient(envelope.to)
        request = build_envelope_request(
            self.adapter, phone_number_id=self.phone_number_id, envelope=envelope
        )
        response = self.transport.send(request)
        result = parse_send_result(self.adapter, to=envelope.to, response=response)
        persist_outbound(
            message_store=self.message_store,
            conversation_store=self.conversation_store,
            tenant_id=self.tenant_id,
            phone_number_id=self.phone_number_id,
            envelope=envelope,
            result=result,
        )
        return result

    def send_text(
        self, *, to: str, body: str, preview_url: bool = True, reply_to: Optional[str] = None
    ) -> SendMessageResult:
        """Send a text message.

        Args:
            to: Destination identifier.
            body: UTF-8 body.
            preview_url: Whether URLs generate link previews.
            reply_to: Optional parent message for contextual replies.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, m.TextMessage(body=body, preview_url=preview_url), reply_to))

    def send_image(
        self,
        *,
        to: str,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> SendMessageResult:
        """Send an image message.

        Args:
            to: Destination identifier.
            media_id: Uploaded media ID.
            media_link: Direct media URL.
            caption: Optional caption.
            reply_to: Optional parent message.

        Returns:
            Typed result.
        """
        return self.send(
            _envelope(
                to,
                m.ImageMessage(media_id=media_id, media_link=media_link, caption=caption),
                reply_to,
            )
        )

    def send_video(
        self,
        *,
        to: str,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> SendMessageResult:
        """Send a video message.

        Args:
            to: Destination identifier.
            media_id: Uploaded media ID.
            media_link: Direct media URL.
            caption: Optional caption.
            reply_to: Optional parent message.

        Returns:
            Typed result.
        """
        return self.send(
            _envelope(
                to,
                m.VideoMessage(media_id=media_id, media_link=media_link, caption=caption),
                reply_to,
            )
        )

    def send_audio(
        self,
        *,
        to: str,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> SendMessageResult:
        """Send an audio message.

        Args:
            to: Destination identifier.
            media_id: Uploaded media ID.
            media_link: Direct media URL.
            reply_to: Optional parent message.

        Returns:
            Typed result.
        """
        return self.send(
            _envelope(to, m.AudioMessage(media_id=media_id, media_link=media_link), reply_to)
        )

    def send_document(
        self,
        *,
        to: str,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        filename: Optional[str] = None,
        caption: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> SendMessageResult:
        """Send a document message.

        Args:
            to: Destination identifier.
            media_id: Uploaded media ID.
            media_link: Direct media URL.
            filename: Optional filename.
            caption: Optional caption.
            reply_to: Optional parent message.

        Returns:
            Typed result.
        """
        return self.send(
            _envelope(
                to,
                m.DocumentMessage(
                    media_id=media_id, media_link=media_link, filename=filename, caption=caption
                ),
                reply_to,
            )
        )

    def send_sticker(
        self,
        *,
        to: str,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        reply_to: Optional[str] = None,
    ) -> SendMessageResult:
        """Send a sticker message.

        Args:
            to: Destination identifier.
            media_id: Uploaded media ID.
            media_link: Direct media URL.
            reply_to: Optional parent message.

        Returns:
            Typed result.
        """
        return self.send(
            _envelope(to, m.StickerMessage(media_id=media_id, media_link=media_link), reply_to)
        )

    def send_reaction(self, *, to: str, message_id: str, emoji: str) -> SendMessageResult:
        """Send a message reaction.

        Args:
            to: Destination identifier.
            message_id: Target message.
            emoji: Emoji, or empty string to remove.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, m.ReactionMessage(message_id=message_id, emoji=emoji)))

    def send_location(
        self,
        *,
        to: str,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> SendMessageResult:
        """Send a location message.

        Args:
            to: Destination identifier.
            latitude: Degrees, -90 to 90.
            longitude: Degrees, -180 to 180.
            name: Optional place name.
            address: Optional address.

        Returns:
            Typed result.
        """
        return self.send(
            _envelope(
                to,
                m.LocationMessage(
                    latitude=latitude, longitude=longitude, name=name, address=address
                ),
            )
        )

    def send_contacts(self, *, to: str, contacts: list[dict[str, Any]]) -> SendMessageResult:
        """Send a contact list message.

        Args:
            to: Destination identifier.
            contacts: Non-empty contact list.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, m.ContactsMessage(contacts=contacts)))

    def send_template(
        self,
        *,
        to: str,
        template_name: str,
        language_code: str,
        components: Optional[list[dict[str, Any]]] = None,
    ) -> SendMessageResult:
        """Send a template message.

        Args:
            to: Destination identifier.
            template_name: Approved template name.
            language_code: Locale such as ``"en_US"``.
            components: Optional components.

        Returns:
            Typed result.
        """
        return self.send(
            _envelope(
                to,
                m.TemplateMessage(
                    template_name=template_name,
                    language_code=language_code,
                    components=components or [],
                ),
            )
        )

    def send_list(self, *, to: str, content: m.ListMessage) -> SendMessageResult:
        """Send an interactive list message.

        Args:
            to: Destination identifier.
            content: Validated list content.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, content))

    def send_reply_buttons(self, *, to: str, content: m.ReplyButtonsMessage) -> SendMessageResult:
        """Send a reply-button message.

        Args:
            to: Destination identifier.
            content: Validated button content.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, content))

    def send_cta(self, *, to: str, content: m.CTAMessage) -> SendMessageResult:
        """Send a call-to-action message.

        Args:
            to: Destination identifier.
            content: Validated CTA content.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, content))

    def send_flow(self, *, to: str, content: m.FlowMessage) -> SendMessageResult:
        """Send a flow message.

        Args:
            to: Destination identifier.
            content: Validated flow content.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, content))

    def send_address(self, *, to: str, content: m.AddressMessage) -> SendMessageResult:
        """Send an address message.

        Args:
            to: Destination identifier.
            content: Validated address content.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, content))

    def send_location_request(self, *, to: str, body_text: str) -> SendMessageResult:
        """Send a location-request message.

        Args:
            to: Destination identifier.
            body_text: Body text.

        Returns:
            Typed result.
        """
        return self.send(_envelope(to, m.LocationRequestMessage(body_text=body_text)))

    def send_typing(self, *, message_id: str) -> SendMessageResult:
        """Show a typing indicator against an inbound message.

        Per Meta's API the indicator rides on a mark-read; the legacy
        standalone typing payload is rejected.

        Args:
            message_id: Inbound message to acknowledge with typing shown.

        Returns:
            Typed result.
        """
        payload = serialize_typing(m.TypingIndicator(message_id=message_id))
        request = Request(
            method="POST",
            path=self.adapter.messages_path(self.phone_number_id),
            json_body=payload,
        )
        response = self.transport.send(request)
        return parse_send_result(self.adapter, to="", response=response)

    def mark_read(self, *, message_id: str) -> SendMessageResult:
        """Mark a message as read.

        Args:
            message_id: Message to mark.

        Returns:
            Typed result.
        """
        payload = serialize_mark_read(m.MarkRead(message_id=message_id))
        request = Request(
            method="POST",
            path=self.adapter.messages_path(self.phone_number_id),
            json_body=payload,
        )
        response = self.transport.send(request)
        return parse_send_result(self.adapter, to="", response=response)


class AsyncMessageService:
    """Asynchronous message operations sharing sync serialization.

    Attributes:
        adapter: Version adapter for serialization.
        transport: Shared pooled async transport.
        phone_number_id: Sender phone number ID.
        message_store: Optional repository receiving outbound records.
        conversation_store: Optional repository receiving conversation records.
        tenant_id: Tenant attached to persisted records.
    """

    def __init__(
        self,
        adapter: VersionAdapter,
        transport: AsyncTransport,
        phone_number_id: str,
        *,
        message_store: Any = None,
        conversation_store: Any = None,
        tenant_id: str = "default",
    ) -> None:
        """Initialize the service.

        Args:
            adapter: Version adapter for serialization.
            transport: Shared pooled async transport.
            phone_number_id: Sender phone number ID.
            message_store: Optional repository receiving outbound records.
            conversation_store: Optional repository receiving conversation records.
            tenant_id: Tenant attached to persisted records.
        """
        self.adapter = adapter
        self.transport = transport
        self.phone_number_id = phone_number_id
        self.message_store = message_store
        self.conversation_store = conversation_store
        self.tenant_id = tenant_id

    async def send(self, envelope: m.OutboundMessage) -> SendMessageResult:
        """Send a typed envelope.

        Args:
            envelope: Outbound message.

        Returns:
            Typed result with the Meta message identifier.
        """
        envelope.to = normalize_recipient(envelope.to)
        request = build_envelope_request(
            self.adapter, phone_number_id=self.phone_number_id, envelope=envelope
        )
        response = await self.transport.asend(request)
        result = parse_send_result(self.adapter, to=envelope.to, response=response)
        persist_outbound(
            message_store=self.message_store,
            conversation_store=self.conversation_store,
            tenant_id=self.tenant_id,
            phone_number_id=self.phone_number_id,
            envelope=envelope,
            result=result,
        )
        return result

    async def send_text(
        self, *, to: str, body: str, preview_url: bool = True, reply_to: Optional[str] = None
    ) -> SendMessageResult:
        """Send a text message.

        Args:
            to: Destination identifier.
            body: UTF-8 body.
            preview_url: Whether URLs generate link previews.
            reply_to: Optional parent message for contextual replies.

        Returns:
            Typed result.
        """
        return await self.send(
            _envelope(to, m.TextMessage(body=body, preview_url=preview_url), reply_to)
        )

    async def send_template(
        self,
        *,
        to: str,
        template_name: str,
        language_code: str,
        components: Optional[list[dict[str, Any]]] = None,
    ) -> SendMessageResult:
        """Send a template message.

        Args:
            to: Destination identifier.
            template_name: Approved template name.
            language_code: Locale such as ``"en_US"``.
            components: Optional components.

        Returns:
            Typed result.
        """
        return await self.send(
            _envelope(
                to,
                m.TemplateMessage(
                    template_name=template_name,
                    language_code=language_code,
                    components=components or [],
                ),
            )
        )

    async def mark_read(self, *, message_id: str) -> SendMessageResult:
        """Mark a message as read.

        Args:
            message_id: Message to mark.

        Returns:
            Typed result.
        """
        payload = serialize_mark_read(m.MarkRead(message_id=message_id))
        request = Request(
            method="POST",
            path=self.adapter.messages_path(self.phone_number_id),
            json_body=payload,
        )
        response = await self.transport.asend(request)
        return parse_send_result(self.adapter, to="", response=response)


__all__ = [
    "AsyncMessageService",
    "MessageService",
    "build_envelope_request",
    "persist_outbound",
]
