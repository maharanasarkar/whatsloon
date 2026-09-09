"""Canonical version-agnostic message serializers.

These pure functions produce the exact wire shapes of the 2.x builders,
including historical anomalies (contacts/typing omit ``recipient_type``;
read receipts omit ``to``/``type``). Version adapters delegate here; future
version diffs override in adapter subclasses only.
"""

from __future__ import annotations

from typing import Any, Optional

from whatsloon.messages import models as m


def _base(
    to: str, kind: str, body: dict[str, Any], recipient_type: str = "individual"
) -> dict[str, Any]:
    """Build the common message envelope.

    Args:
        to: Destination identifier.
        kind: Message type key.
        body: Type-specific content.
        recipient_type: Either ``"individual"`` or ``"group"``.

    Returns:
        Full wire payload.
    """
    return {
        "messaging_product": "whatsapp",
        "recipient_type": recipient_type,
        "to": to,
        "type": kind,
        kind: body,
    }


def serialize_text(to: str, content: m.TextMessage) -> dict[str, Any]:
    """Serialize a text message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    payload = _base(to, "text", {"preview_url": content.preview_url, "body": content.body})
    return payload


def _media_block(content: Any) -> dict[str, Any]:
    """Serialize shared media reference fields.

    Args:
        content: Media content model.

    Returns:
        Media block with set fields only.
    """
    block: dict[str, Any] = {}
    if getattr(content, "media_id", None):
        block["id"] = content.media_id
    if getattr(content, "media_link", None):
        block["link"] = content.media_link
    if getattr(content, "caption", None) is not None and getattr(content, "caption", None):
        block["caption"] = content.caption
    return block


def serialize_image(to: str, content: m.ImageMessage) -> dict[str, Any]:
    """Serialize an image message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return _base(to, "image", _media_block(content))


def serialize_video(to: str, content: m.VideoMessage) -> dict[str, Any]:
    """Serialize a video message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return _base(to, "video", _media_block(content))


def serialize_audio(to: str, content: m.AudioMessage) -> dict[str, Any]:
    """Serialize an audio message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return _base(to, "audio", _media_block(content))


def serialize_document(to: str, content: m.DocumentMessage) -> dict[str, Any]:
    """Serialize a document message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    block = _media_block(content)
    if content.filename:
        block["filename"] = content.filename
    return _base(to, "document", block)


def serialize_sticker(to: str, content: m.StickerMessage) -> dict[str, Any]:
    """Serialize a sticker message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return _base(to, "sticker", _media_block(content))


def serialize_reaction(to: str, content: m.ReactionMessage) -> dict[str, Any]:
    """Serialize a reaction message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return _base(to, "reaction", {"message_id": content.message_id, "emoji": content.emoji})


def serialize_location(to: str, content: m.LocationMessage) -> dict[str, Any]:
    """Serialize a location message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    block: dict[str, Any] = {"latitude": content.latitude, "longitude": content.longitude}
    if content.name:
        block["name"] = content.name
    if content.address:
        block["address"] = content.address
    return _base(to, "location", block)


def serialize_contacts(to: str, content: m.ContactsMessage) -> dict[str, Any]:
    """Serialize a contacts message (no ``recipient_type``, legacy parity).

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "contacts",
        "contacts": content.contacts,
    }


def serialize_template(to: str, content: m.TemplateMessage) -> dict[str, Any]:
    """Serialize a template message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    template: dict[str, Any] = {
        "name": content.template_name,
        "language": {"code": content.language_code},
    }
    if content.components:
        template["components"] = content.components
    return {
        "messaging_product": "whatsapp",
        "recipient_type": content.recipient_type,
        "to": to,
        "type": "template",
        "template": template,
    }


def _interactive_shell(
    to: str,
    interactive_type: str,
    body_text: Optional[str],
    action: dict[str, Any],
    header: Optional[dict[str, Any]] = None,
    footer_text: Optional[str] = None,
) -> dict[str, Any]:
    """Build an interactive payload shell.

    Args:
        to: Destination identifier.
        interactive_type: Interactive subtype.
        body_text: Optional body text.
        action: Action object.
        header: Optional header object.
        footer_text: Optional footer.

    Returns:
        Wire payload.
    """
    interactive: dict[str, Any] = {"type": interactive_type, "action": action}
    if body_text is not None:
        interactive["body"] = {"text": body_text}
    if header is not None:
        interactive["header"] = header
    if footer_text is not None:
        interactive["footer"] = {"text": footer_text}
    # Legacy key order: type, [body], action, [header], [footer].
    ordered: dict[str, Any] = {"type": interactive_type}
    if "body" in interactive:
        ordered["body"] = interactive["body"]
    ordered["action"] = action
    if "header" in interactive:
        ordered["header"] = interactive["header"]
    if "footer" in interactive:
        ordered["footer"] = interactive["footer"]
    return {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "interactive",
        "interactive": ordered,
    }


def serialize_list(to: str, content: m.ListMessage) -> dict[str, Any]:
    """Serialize an interactive list message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return _interactive_shell(
        to,
        "list",
        content.body_text,
        {"button": content.button_text, "sections": content.sections},
        header=content.header,
        footer_text=content.footer_text,
    )


def serialize_reply_buttons(to: str, content: m.ReplyButtonsMessage) -> dict[str, Any]:
    """Serialize a reply-button message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    buttons = [{"type": "reply", "reply": {"id": b.id, "title": b.title}} for b in content.buttons]
    return _interactive_shell(
        to,
        "button",
        content.body_text,
        {"buttons": buttons},
        header=content.header,
        footer_text=content.footer_text,
    )


def serialize_cta(to: str, content: m.CTAMessage) -> dict[str, Any]:
    """Serialize a call-to-action message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return _interactive_shell(
        to,
        "cta_url",
        content.body_text,
        {
            "name": "cta_url",
            "parameters": {"display_text": content.button_text, "url": content.button_url},
        },
        header=content.header,
        footer_text=content.footer_text,
    )


def serialize_flow(to: str, content: m.FlowMessage) -> dict[str, Any]:
    """Serialize a flow message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    parameters: dict[str, Any] = {
        "flow_message_version": content.flow_message_version,
        "flow_token": content.flow_token,
        "flow_id": content.flow_id,
        "flow_cta": content.flow_cta,
        "flow_action": content.flow_action,
    }
    if content.flow_action_payload is not None:
        parameters["flow_action_payload"] = content.flow_action_payload
    return _interactive_shell(
        to,
        "flow",
        content.body_text,
        {"name": "flow", "parameters": parameters},
        header=content.header,
        footer_text=content.footer_text,
    )


def serialize_address(to: str, content: m.AddressMessage) -> dict[str, Any]:
    """Serialize an address message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    parameters: dict[str, Any] = {"country": content.country_iso_code}
    if content.values is not None:
        parameters["values"] = content.values
    if content.validation_errors is not None:
        parameters["validation_errors"] = content.validation_errors
    if content.saved_addresses is not None:
        parameters["saved_addresses"] = content.saved_addresses
    return _interactive_shell(
        to,
        "address_message",
        content.body,
        {"name": "address_message", "parameters": parameters},
        header={"type": "text", "text": content.header} if content.header else None,
        footer_text=content.footer,
    )


def serialize_location_request(to: str, content: m.LocationRequestMessage) -> dict[str, Any]:
    """Serialize a location-request message.

    Args:
        to: Destination identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    return _interactive_shell(
        to,
        "location_request_message",
        content.body_text,
        {"name": "send_location"},
    )


def serialize_typing(content: m.TypingIndicator) -> dict[str, Any]:
    """Serialize a typing indicator per Meta's read+indicator shape.

    The indicator attaches to a mark-read of an inbound message; the
    legacy standalone ``type: typing`` payload is rejected by Meta.

    Args:
        content: Typed content.

    Returns:
        Wire payload.
    """
    return {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": content.message_id,
        "typing_indicator": {"type": "text"},
    }


def serialize_mark_read(content: m.MarkRead) -> dict[str, Any]:
    """Serialize a read receipt (no ``to``/``type``, legacy parity).

    Args:
        content: Typed content.

    Returns:
        Wire payload.
    """
    return {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": content.message_id,
    }


def serialize_pin(to: str, content: m.PinMessage) -> dict[str, Any]:
    """Serialize a group pin/unpin operation.

    Args:
        to: Group identifier.
        content: Typed content.

    Returns:
        Wire payload.
    """
    block: dict[str, Any] = {"type": content.operation, "message_id": content.message_id}
    if content.operation == "pin":
        block["expiration_days"] = content.expiration_days
    return _base(to, "pin", block, "group")


_CONTENT_SERIALIZERS: dict[str, Any] = {
    "TextMessage": serialize_text,
    "ImageMessage": serialize_image,
    "VideoMessage": serialize_video,
    "AudioMessage": serialize_audio,
    "DocumentMessage": serialize_document,
    "StickerMessage": serialize_sticker,
    "ReactionMessage": serialize_reaction,
    "LocationMessage": serialize_location,
    "ContactsMessage": serialize_contacts,
    "TemplateMessage": serialize_template,
    "ListMessage": serialize_list,
    "ReplyButtonsMessage": serialize_reply_buttons,
    "CTAMessage": serialize_cta,
    "FlowMessage": serialize_flow,
    "AddressMessage": serialize_address,
    "LocationRequestMessage": serialize_location_request,
    "PinMessage": serialize_pin,
}
"""Content serializers keyed by model class name."""


def serialize_envelope(envelope: m.OutboundMessage) -> dict[str, Any]:
    """Serialize an outbound envelope, injecting reply context when set.

    Group envelopes override ``recipient_type``; tracking data passes
    through as ``biz_opaque_callback_data``.

    Args:
        envelope: Envelope with recipient and typed content.

    Returns:
        Wire payload.

    Raises:
        TypeError: If the content type is not sendable.
    """
    name = type(envelope.content).__name__
    serializer = _CONTENT_SERIALIZERS.get(name)
    if serializer is None:
        raise TypeError(f"Unsupported message content: {name}.")
    payload: dict[str, Any] = serializer(envelope.to, envelope.content)
    if "recipient_type" in payload:
        payload["recipient_type"] = envelope.recipient_type
    if envelope.biz_opaque_callback_data:
        payload["biz_opaque_callback_data"] = envelope.biz_opaque_callback_data
    if envelope.reply_to_message_id:
        payload["context"] = {"message_id": envelope.reply_to_message_id}
    return payload
