"""Message model validation tests mirroring 2.x limits."""

import pytest
from pydantic import ValidationError

from whatsloon.messages.builders import ButtonsBuilder, ListBuilder
from whatsloon.messages.models import (
    AudioMessage,
    ContactsMessage,
    DocumentMessage,
    ImageMessage,
    ListMessage,
    LocationMessage,
    OutboundMessage,
    ReplyButtonsMessage,
    TextMessage,
    TypingStatus,
)


def test_text_body_limits():
    """Text bodies follow the 1-4096 contract."""
    assert TextMessage(body="Hi").preview_url is True
    with pytest.raises(ValidationError):
        TextMessage(body="")
    with pytest.raises(ValidationError):
        TextMessage(body="x" * 4097)


def test_media_requires_source():
    """Media without id or link is rejected like the 2.x builder."""
    with pytest.raises(ValidationError):
        ImageMessage()
    assert ImageMessage(media_id="123", caption="Hi").caption == "Hi"
    with pytest.raises(ValidationError):
        AudioMessage()


def test_document_parity_quirk():
    """A lone filename passes, reproducing the 2.x empty-dict check."""
    assert DocumentMessage(filename="a.pdf").filename == "a.pdf"
    with pytest.raises(ValidationError):
        DocumentMessage()


def test_location_ranges():
    """Coordinates enforce Meta ranges."""
    assert LocationMessage(latitude=1.0, longitude=2.0).latitude == 1.0
    with pytest.raises(ValidationError):
        LocationMessage(latitude=91.0, longitude=0.0)
    with pytest.raises(ValidationError):
        LocationMessage(latitude=0.0, longitude=181.0)


def test_contacts_require_non_empty_list():
    """Contacts reject empty lists like the 2.x builder."""
    with pytest.raises(ValidationError):
        ContactsMessage(contacts=[])
    assert len(ContactsMessage(contacts=[{"name": "A"}]).contacts) == 1


def test_list_limits():
    """List button/sections/rows limits match 2.x exactly."""
    with pytest.raises(ValidationError):
        ListMessage(body_text="b", button_text="x" * 21, sections=[{"rows": []}])
    rows = [{"id": str(i)} for i in range(11)]
    with pytest.raises(ValidationError):
        ListMessage(body_text="b", button_text="ok", sections=[{"rows": rows}])
    built = ListBuilder("b", "ok").section("s", [{"id": "1"}]).build()
    assert built.sections[0]["title"] == "s"


def test_reply_buttons_limits_and_header():
    """Button count/title/header rules match 2.x exactly."""
    with pytest.raises(ValidationError):
        ReplyButtonsMessage(body_text="b", buttons=[])
    with pytest.raises(ValidationError):
        ReplyButtonsMessage(
            body_text="b",
            buttons=[{"id": "1", "title": "x" * 21}],
        )
    with pytest.raises(ValidationError):
        ReplyButtonsMessage(
            body_text="b",
            buttons=[{"id": "1", "title": "ok"}],
            header={"type": "audio"},
        )
    built = ButtonsBuilder("b").button("1", "Yes").build()
    assert built.buttons[0].title == "Yes"


def test_typing_status_values():
    """Only typing/paused statuses are accepted."""
    assert TypingStatus(status="typing").status == "typing"
    with pytest.raises(ValidationError):
        TypingStatus(status="idle")


def test_envelope_reply_to_rejects_empty():
    """Empty reply identifiers fail like the 2.x contextual builder."""
    envelope = OutboundMessage(to="919", content=TextMessage(body="Hi"), reply_to_message_id="w-1")
    assert envelope.reply_to_message_id == "w-1"
    with pytest.raises(TypeError):
        OutboundMessage(to="919", content=TextMessage(body="Hi"), reply_to_message_id="")
