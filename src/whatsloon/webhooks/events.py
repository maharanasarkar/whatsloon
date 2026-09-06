"""Normalized inbound webhook events.

Parsing never drops data: unrecognized shapes become :class:`UnknownEvent`
with the raw envelope preserved for later handling.
"""

from __future__ import annotations

from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field


class WebhookMessageReceived(BaseModel):
    """Normalized inbound message event.

    Attributes:
        event_type: Always ``"message.received"``.
        api_version: Adapter version used for normalization.
        message_id: Meta message identifier.
        sender: Sender identifier.
        recipient_phone_id: Destination phone number ID.
        timestamp: Meta timestamp string.
        message_type: Meta message type such as ``"text"``.
        text_body: Plain text when present.
        raw: Preserved raw message object.
    """

    event_type: Literal["message.received"] = "message.received"
    api_version: str = ""
    message_id: str = ""
    sender: str = ""
    recipient_phone_id: str = ""
    timestamp: str = ""
    message_type: str = ""
    text_body: Optional[str] = None
    raw: dict[str, Any] = Field(default_factory=dict)


class WebhookMessageStatus(BaseModel):
    """Normalized delivery status event.

    Attributes:
        event_type: Always ``"message.status"``.
        api_version: Adapter version used for normalization.
        message_id: Meta message identifier.
        status: Status such as ``"delivered"`` or ``"read"``.
        recipient: Recipient identifier.
        timestamp: Meta timestamp string.
        raw: Preserved raw status object.
    """

    event_type: Literal["message.status"] = "message.status"
    api_version: str = ""
    message_id: str = ""
    status: str = ""
    recipient: str = ""
    timestamp: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


class UnknownEvent(BaseModel):
    """Preserved unrecognized webhook content.

    Attributes:
        event_type: Always ``"unknown"``.
        api_version: Adapter version used for normalization.
        reason: Why the content was not recognized.
        raw: Full raw envelope.
    """

    event_type: Literal["unknown"] = "unknown"
    api_version: str = ""
    reason: str = ""
    raw: dict[str, Any] = Field(default_factory=dict)


NormalizedEvent = Union[WebhookMessageReceived, WebhookMessageStatus, UnknownEvent]
"""Any normalized inbound event."""
