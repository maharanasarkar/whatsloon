"""Parity tests: new serializers must equal legacy builder output.

Each case calls a 2.x ``_build_*_payload`` method and the matching v3
serializer with identical inputs and asserts dict equality, on both
adapters where applicable.
"""

import pytest

from whatsloon import WhatsAppCloudAPIClient
from whatsloon.api_versions.registry import get_adapter
from whatsloon.messages import models as m
from whatsloon.messages.serializers import (
    serialize_address,
    serialize_audio,
    serialize_contacts,
    serialize_cta,
    serialize_document,
    serialize_envelope,
    serialize_flow,
    serialize_image,
    serialize_list,
    serialize_location,
    serialize_location_request,
    serialize_mark_read,
    serialize_reaction,
    serialize_reply_buttons,
    serialize_sticker,
    serialize_template,
    serialize_text,
    serialize_typing,
    serialize_video,
)

TO = "919876543210"


@pytest.fixture(scope="module")
def legacy():
    """Build a legacy client bound to the parity recipient.

    Returns:
        Legacy composed client.
    """
    return WhatsAppCloudAPIClient(
        access_token="test",
        phone_number_id="123",
        recipient_country_code="91",
        recipient_mobile_number="9876543210",
    )


def test_text_parity(legacy):
    """Text payloads match on both adapters."""
    expected = legacy._build_text_payload("Hello!", preview_url=True)
    for version in ("v19.0", "v26.0"):
        adapter = get_adapter(version)
        assert adapter.build_text_payload(to=TO, body="Hello!", preview_url=True) == expected
    assert serialize_text(TO, m.TextMessage(body="Hello!", preview_url=True)) == expected


def test_media_parity(legacy):
    """Image/video/audio/document/sticker payloads match."""
    assert serialize_image(
        TO, m.ImageMessage(media_id="mid", caption="cap")
    ) == legacy._build_image_payload(media_id="mid", caption="cap")
    assert serialize_video(
        TO, m.VideoMessage(media_link="https://x/v.mp4")
    ) == legacy._build_video_payload(media_link="https://x/v.mp4")
    assert serialize_audio(TO, m.AudioMessage(media_id="mid")) == legacy._build_audio_payload(
        media_id="mid"
    )
    assert serialize_document(
        TO, m.DocumentMessage(media_id="mid", filename="a.pdf", caption="cap")
    ) == legacy._build_document_payload(media_id="mid", filename="a.pdf", caption="cap")
    assert serialize_sticker(
        TO, m.StickerMessage(media_link="https://x/s.webp")
    ) == legacy._build_sticker_payload(media_link="https://x/s.webp")


def test_reaction_location_contacts_parity(legacy):
    """Reaction/location/contacts payloads match, anomalies included."""
    assert serialize_reaction(
        TO, m.ReactionMessage(message_id="w-1", emoji="👍")
    ) == legacy._build_reaction_payload(message_id="w-1", emoji="👍")
    assert serialize_location(
        TO, m.LocationMessage(latitude=12.9, longitude=77.6, name="N", address="A")
    ) == legacy._build_location_payload(latitude=12.9, longitude=77.6, name="N", address="A")
    contacts = [{"name": {"first_name": "A"}, "phones": [{"phone": "+919876543210"}]}]
    assert serialize_contacts(
        TO, m.ContactsMessage(contacts=contacts)
    ) == legacy._build_contact_payload(contacts=contacts)


def test_template_parity(legacy):
    """Template payloads match with and without components."""
    components = [{"type": "body", "parameters": [{"type": "text", "text": "Hi"}]}]
    assert serialize_template(
        TO, m.TemplateMessage(template_name="hello", language_code="en_US", components=components)
    ) == legacy._build_template_payload(
        template_name="hello", language_code="en_US", components=components
    )
    assert serialize_template(
        TO, m.TemplateMessage(template_name="hello", language_code="en_US")
    ) == legacy._build_template_payload(template_name="hello", language_code="en_US")


def test_interactive_parity(legacy):
    """List/buttons/CTA/flow/address/location-request payloads match."""
    sections = [{"title": "s", "rows": [{"id": "1", "title": "One"}]}]
    assert serialize_list(
        TO, m.ListMessage(body_text="b", button_text="Menu", sections=sections)
    ) == legacy._build_list_payload(body_text="b", button_text="Menu", sections=sections)
    buttons = [{"type": "reply", "reply": {"id": "1", "title": "Yes"}}]
    assert serialize_reply_buttons(
        TO,
        m.ReplyButtonsMessage(body_text="b", buttons=[m.ReplyButton(id="1", title="Yes")]),
    ) == legacy._build_reply_buttons_payload(body_text="b", buttons=buttons)
    assert serialize_cta(
        TO, m.CTAMessage(body_text="b", button_text="Open", button_url="https://x")
    ) == legacy._build_cta_payload(body_text="b", button_text="Open", button_url="https://x")
    assert serialize_flow(
        TO,
        m.FlowMessage(flow_token="tok", flow_id="fid", flow_cta="Start", flow_action="navigate"),
    ) == legacy._build_flow_payload(
        flow_token="tok", flow_id="fid", flow_cta="Start", flow_action="navigate"
    )
    assert serialize_address(
        TO, m.AddressMessage(body="b", country_iso_code="IN")
    ) == legacy._build_address_payload(body="b", country_iso_code="IN")
    assert serialize_location_request(
        TO, m.LocationRequestMessage(body_text="Share?")
    ) == legacy._build_location_request_payload(body_text="Share?")


def test_operations_parity(legacy):
    """Typing and read-receipt payloads match, anomalies included."""
    assert serialize_typing(
        TO, m.TypingStatus(status="typing")
    ) == legacy._build_typing_indicator_payload(status="typing")
    assert serialize_mark_read(m.MarkRead(message_id="w-1")) == legacy._build_read_payload(
        message_id="w-1"
    )


def test_envelope_context_parity(legacy):
    """Reply envelopes inject context exactly like contextual replies."""
    content = {"preview_url": False, "body": "Hi"}
    expected = legacy._build_contextual_reply_payload(
        reply_to_message_id="w-9", message_type="text", message_content=content
    )
    envelope = m.OutboundMessage(
        to=TO, content=m.TextMessage(body="Hi", preview_url=False), reply_to_message_id="w-9"
    )
    assert serialize_envelope(envelope) == expected


def test_envelope_without_reply_has_no_context():
    """Plain envelopes carry no context block."""
    envelope = m.OutboundMessage(to=TO, content=m.TextMessage(body="Hi"))
    payload = serialize_envelope(envelope)
    assert "context" not in payload
    assert payload["to"] == TO
