"""Typed message content models.

Every 2.x sender type has a Pydantic model here. Validation mirrors the
legacy builders exactly (same limits, same failure modes) so parity tests
prove identical behavior; stricter Meta limits are deferred debt.
"""

from __future__ import annotations

from typing import Any, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class TextMessage(BaseModel):
    """Plain text message.

    Attributes:
        body: UTF-8 body (1-4096 chars).
        preview_url: Whether URLs generate link previews.
    """

    body: str = Field(min_length=1, max_length=4096)
    preview_url: bool = True


class MediaSource(BaseModel):
    """Shared media reference for image/video/audio/document/sticker.

    Attributes:
        media_id: Uploaded media ID (recommended).
        media_link: Direct media URL.
    """

    media_id: Optional[str] = None
    media_link: Optional[str] = None

    @model_validator(mode="after")
    def _require_source(self) -> MediaSource:
        """Require at least one media source.

        Returns:
            This instance.

        Raises:
            ValueError: If neither source is provided.
        """
        if not self.media_id and not self.media_link:
            raise ValueError("Provide either media_id or media_link.")
        return self


class ImageMessage(MediaSource):
    """Image message with optional caption.

    Attributes:
        caption: Optional caption.
    """

    caption: Optional[str] = None


class VideoMessage(MediaSource):
    """Video message with optional caption.

    Attributes:
        caption: Optional caption.
    """

    caption: Optional[str] = None


class AudioMessage(MediaSource):
    """Audio message."""


class DocumentMessage(BaseModel):
    """Document message.

    Attributes:
        media_id: Uploaded media ID.
        media_link: Direct media URL.
        filename: Optional filename.
        caption: Optional caption.
    """

    media_id: Optional[str] = None
    media_link: Optional[str] = None
    filename: Optional[str] = None
    caption: Optional[str] = None

    @model_validator(mode="after")
    def _require_content(self) -> DocumentMessage:
        """Require at least one document field (legacy parity quirk).

        The 2.x builder only rejects a fully empty document dict, so a
        lone filename passes; this validator reproduces that behavior.

        Returns:
            This instance.

        Raises:
            ValueError: If all fields are empty.
        """
        if not any([self.media_id, self.media_link, self.filename, self.caption]):
            raise ValueError(
                "Provide document content (media_id, media_link, filename, or caption)."
            )
        return self


class StickerMessage(MediaSource):
    """Sticker message."""


class ReactionMessage(BaseModel):
    """Reaction to a message; empty emoji removes the reaction.

    Attributes:
        message_id: Target message identifier.
        emoji: Emoji, or empty string to remove.
    """

    message_id: str = Field(min_length=1)
    emoji: str = ""


class LocationMessage(BaseModel):
    """Location message with coordinate validation.

    Attributes:
        latitude: Degrees, -90 to 90.
        longitude: Degrees, -180 to 180.
        name: Optional place name.
        address: Optional address.
    """

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    name: Optional[str] = None
    address: Optional[str] = None


class ContactsMessage(BaseModel):
    """Contact list message.

    Attributes:
        contacts: Non-empty list of Meta contact objects. Meta requires
            ``name.formatted_name`` on every contact.
    """

    contacts: list[dict[str, Any]] = Field(min_length=1)

    @field_validator("contacts")
    @classmethod
    def _require_formatted_names(cls, contacts: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Require Meta's mandatory formatted names.

        Args:
            contacts: Candidate contact list.

        Returns:
            The list unchanged.

        Raises:
            ValueError: If any contact lacks ``name.formatted_name``.
        """
        for contact in contacts:
            name = contact.get("name") if isinstance(contact, dict) else None
            if not isinstance(name, dict) or not name.get("formatted_name"):
                raise ValueError("Every contact requires name.formatted_name.")
        return contacts


class TemplateComponent(BaseModel):
    """Template component placeholder.

    Attributes:
        type: Component type such as ``"body"``.
        parameters: Component parameters.
    """

    model_config = {"extra": "allow"}

    type: str
    parameters: list[dict[str, Any]] = Field(default_factory=list)


class TemplateMessage(BaseModel):
    """Template message.

    Attributes:
        template_name: Approved template name.
        language_code: Locale such as ``"en_US"``.
        components: Optional component list.
        recipient_type: Recipient type, defaults to individual.
    """

    template_name: str = Field(min_length=1)
    language_code: str = Field(min_length=1)
    components: list[dict[str, Any]] = Field(default_factory=list)
    recipient_type: str = "individual"


class ListSection(BaseModel):
    """Interactive list section.

    Attributes:
        title: Section title.
        rows: Section rows.
    """

    model_config = {"extra": "allow"}

    title: str = ""
    rows: list[dict[str, Any]] = Field(default_factory=list)


class ListMessage(BaseModel):
    """Interactive list message with 2.x limits enforced.

    Attributes:
        body_text: Body text.
        button_text: Button label, max 20 chars.
        sections: Max 10 sections, max 10 rows total.
        header: Optional header object.
        footer_text: Optional footer.
    """

    body_text: str = Field(min_length=1)
    button_text: str = Field(min_length=1, max_length=20)
    sections: list[dict[str, Any]] = Field(min_length=1, max_length=10)
    header: Optional[dict[str, Any]] = None
    footer_text: Optional[str] = None

    @model_validator(mode="after")
    def _limit_rows(self) -> ListMessage:
        """Enforce the 10-row total limit.

        Returns:
            This instance.

        Raises:
            ValueError: If sections hold more than 10 rows.
        """
        total = sum(len(section.get("rows", [])) for section in self.sections)
        if total > 10:
            raise ValueError("List sections hold at most 10 rows in total.")
        return self


class ReplyButton(BaseModel):
    """Single reply button with title limit.

    Attributes:
        id: Button identifier.
        title: Button title, max 20 chars.
    """

    id: str = Field(min_length=1)
    title: str = Field(min_length=1, max_length=20)


class ReplyButtonsMessage(BaseModel):
    """Reply-button message with 2.x limits enforced.

    Attributes:
        body_text: Body text.
        buttons: One to three buttons.
        header: Optional header; type must be text/image/video/document.
        footer_text: Optional footer.
    """

    body_text: str = Field(min_length=1)
    buttons: list[ReplyButton] = Field(min_length=1, max_length=3)
    header: Optional[dict[str, Any]] = None
    footer_text: Optional[str] = None

    @field_validator("header")
    @classmethod
    def _check_header(cls, header: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        """Validate the header object type.

        Args:
            header: Header object, if any.

        Returns:
            The header unchanged.

        Raises:
            ValueError: If the header type is unsupported.
        """
        if header is not None and header.get("type") not in ("text", "image", "video", "document"):
            raise ValueError("Header type must be text, image, video, or document.")
        return header


class CTAMessage(BaseModel):
    """Call-to-action URL message.

    Attributes:
        body_text: Body text.
        button_text: Button label.
        button_url: Target URL.
        header: Optional header object.
        footer_text: Optional footer.
    """

    body_text: str = Field(min_length=1)
    button_text: str = Field(min_length=1)
    button_url: str = Field(min_length=1)
    header: Optional[dict[str, Any]] = None
    footer_text: Optional[str] = None


class FlowMessage(BaseModel):
    """Flow message.

    Attributes:
        flow_token: Flow token.
        flow_id: Flow ID.
        flow_cta: CTA label.
        flow_action: Action such as ``"navigate"``.
        flow_message_version: Message version, defaults to ``"3"``.
        body_text: Optional body.
        header: Optional header object.
        footer_text: Optional footer.
        flow_action_payload: Optional action payload.
    """

    flow_token: str = Field(min_length=1)
    flow_id: str = Field(min_length=1)
    flow_cta: str = Field(min_length=1)
    flow_action: str = Field(min_length=1)
    flow_message_version: str = "3"
    body_text: Optional[str] = None
    header: Optional[dict[str, Any]] = None
    footer_text: Optional[str] = None
    flow_action_payload: Optional[dict[str, Any]] = None


class AddressMessage(BaseModel):
    """Address-collection message.

    Attributes:
        body: Body text.
        country_iso_code: ISO country for address configuration.
        header: Optional header text.
        footer: Optional footer text.
        values: Optional prefill values.
        validation_errors: Optional validation errors.
        saved_addresses: Optional saved addresses.
    """

    body: str = Field(min_length=1)
    country_iso_code: str = Field(min_length=1)
    header: Optional[str] = None
    footer: Optional[str] = None
    values: Optional[dict[str, Any]] = None
    validation_errors: Optional[dict[str, Any]] = None
    saved_addresses: Optional[list[dict[str, Any]]] = None


class LocationRequestMessage(BaseModel):
    """Location-request message.

    Attributes:
        body_text: Body text.
    """

    body_text: str = Field(min_length=1)


class TypingIndicator(BaseModel):
    """Typing indicator operation (not an envelope content type).

    Per Meta's API the indicator rides on a mark-read of an inbound
    message; there is no standalone typing message type.

    Attributes:
        message_id: Inbound message to acknowledge with typing shown.
    """

    message_id: str = Field(min_length=1)


class MarkRead(BaseModel):
    """Read-receipt operation (not an envelope content type).

    Attributes:
        message_id: Message to mark as read.
    """

    message_id: str = Field(min_length=1)


class PinMessage(BaseModel):
    """Group message pin/unpin operation.

    Attributes:
        operation: Either ``"pin"`` or ``"unpin"``.
        message_id: Target message identifier.
        expiration_days: Pin duration, 1-30 days; required when pinning.
    """

    operation: str
    message_id: str = Field(min_length=1)
    expiration_days: Optional[int] = Field(default=None, ge=1, le=30)

    @field_validator("operation")
    @classmethod
    def _check_operation(cls, operation: str) -> str:
        """Validate the pin operation.

        Args:
            operation: Candidate operation.

        Returns:
            The operation unchanged.

        Raises:
            ValueError: If not pin or unpin.
        """
        if operation not in ("pin", "unpin"):
            raise ValueError("Pin operation must be 'pin' or 'unpin'.")
        return operation

    @model_validator(mode="after")
    def _require_expiry(self) -> PinMessage:
        """Require expiry days when pinning.

        Returns:
            This instance.

        Raises:
            ValueError: If pinning without expiry days.
        """
        if self.operation == "pin" and self.expiration_days is None:
            raise ValueError("expiration_days is required when pinning.")
        return self


MessageContent = Union[
    TextMessage,
    ImageMessage,
    VideoMessage,
    AudioMessage,
    DocumentMessage,
    StickerMessage,
    ReactionMessage,
    LocationMessage,
    ContactsMessage,
    TemplateMessage,
    ListMessage,
    ReplyButtonsMessage,
    CTAMessage,
    FlowMessage,
    AddressMessage,
    LocationRequestMessage,
    PinMessage,
]
"""Content types sendable inside an :class:`OutboundMessage` envelope."""


class OutboundMessage(BaseModel):
    """Envelope pairing a recipient with typed content.

    Attributes:
        to: Destination identifier, or group ID when recipient_type is group.
        content: Typed message content.
        reply_to_message_id: Optional parent message for contextual replies.
        recipient_type: Either ``"individual"`` or ``"group"``.
        biz_opaque_callback_data: Optional tracking string echoed in webhooks.
    """

    to: str = Field(min_length=1)
    content: MessageContent
    reply_to_message_id: Optional[str] = None
    recipient_type: str = "individual"
    biz_opaque_callback_data: Optional[str] = None

    @field_validator("reply_to_message_id")
    @classmethod
    def _check_reply_to(cls, value: Optional[str]) -> Optional[str]:
        """Reject empty reply identifiers like the 2.x builder.

        Args:
            value: Candidate parent message ID.

        Returns:
            The value unchanged.

        Raises:
            TypeError: If an empty identifier is supplied.
        """
        if value is not None and not value:
            raise TypeError("reply_to_message_id must be a non-empty identifier.")
        return value

    @field_validator("recipient_type")
    @classmethod
    def _check_recipient_type(cls, value: str) -> str:
        """Validate the recipient type.

        Args:
            value: Candidate recipient type.

        Returns:
            The value unchanged.

        Raises:
            ValueError: If not individual or group.
        """
        if value not in ("individual", "group"):
            raise ValueError("recipient_type must be 'individual' or 'group'.")
        return value
