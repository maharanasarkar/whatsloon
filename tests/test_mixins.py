import pytest
from unittest.mock import MagicMock, patch
from whatsloon.address import AddressSender
from whatsloon.audio import AudioSender
from whatsloon.base import WhatsAppBaseClient
from whatsloon.contact import ContactSender
from whatsloon.document import DocumentSender
from whatsloon.image import ImageSender
from whatsloon.text import TextMessageSender
from whatsloon.flow import FlowSender
from whatsloon.list import ListSender
from whatsloon.reply_buttons import ReplyButtonSender
from whatsloon.location import LocationSender
from whatsloon.location_request import LocationRequestSender
from whatsloon.reaction import ReactionSender
from whatsloon.sticker import StickerSender
from whatsloon.template import TemplateSender
from whatsloon.video import VideoSender
from whatsloon.read_receipts import ReadMark
from whatsloon.contextual_reply import ContextualReply
from whatsloon.typing_indicator import TypingIndicator


class DummyClient(
    FlowSender,
    ListSender,
    ReplyButtonSender,
    LocationSender,
    LocationRequestSender,
    ReactionSender,
    StickerSender,
    TemplateSender,
    VideoSender,
    ReadMark,
    ContextualReply,
    TypingIndicator,
):
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v19.0/FAKE_PHONE_ID/messages"
        self.headers = {"Authorization": "Bearer FAKE_TOKEN"}
        self.recipient_to_send = "1234567890"


@pytest.fixture
def client():
    return DummyClient()


@patch("requests.post")
def test_flow_sender(mock_post, client):
    """
    Test FlowSender _send_request with valid payload and mocked response.
    Input: valid flow payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_flow_payload(
        flow_token="token", flow_id="id", flow_cta="cta", flow_action="navigate"
    )
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_flow_sender_error(mock_post, client):
    """
    Test FlowSender _send_request with HTTP error.
    Input: valid flow payload, mocked requests.post raises HTTPError.
    Output: status_code 400.
    """
    mock_post.return_value.status_code = 400
    mock_post.return_value.json.return_value = {"error": "Bad Request"}
    payload = client._build_flow_payload(
        flow_token="token", flow_id="id", flow_cta="cta", flow_action="navigate"
    )
    result = client._send_request(payload)
    assert result.status_code == 400


@patch("requests.post")
def test_list_sender(mock_post, client):
    """
    Test ListSender _send_request with valid payload and mocked response.
    Input: valid list payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_list_payload(
        body_text="Choose one",
        button_text="Pick",
        sections=[{"title": "A", "rows": [{"id": "1", "title": "Row1"}]}],
    )
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_reply_button_sender(mock_post, client):
    """
    Test ReplyButtonSender _send_request with valid payload and mocked response.
    Input: valid reply button payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_reply_buttons_payload(
        body_text="Reply?",
        buttons=[{"type": "reply", "reply": {"id": "1", "title": "Yes"}}],
    )
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_location_sender(mock_post, client):
    """
    Test LocationSender _send_request with valid payload and mocked response.
    Input: valid location payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_location_payload(
        37.7749, -122.4194, name="SF", address="CA"
    )
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_location_sender_latitude_error(mock_post, client):
    """
    Test LocationSender _build_location_payload with invalid latitude.
    Input: latitude=100 (invalid), longitude=0.
    Output: Raises ValueError.
    """
    with pytest.raises(ValueError):
        client._build_location_payload(100, 0)


@patch("requests.post")
def test_location_request_sender(mock_post, client):
    """
    Test LocationRequestSender _send_request with valid payload and mocked response.
    Input: valid location request payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_location_request_payload("Share location?")
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_reaction_sender(mock_post, client):
    """
    Test ReactionSender _send_request with valid payload and mocked response.
    Input: valid reaction payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_reaction_payload("msgid", "😀")
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_sticker_sender(mock_post, client):
    """
    Test StickerSender _send_request with valid payload and mocked response.
    Input: valid sticker payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_sticker_payload(media_id="mediaid")
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_template_sender(mock_post, client):
    """
    Test TemplateSender _send_request with valid payload and mocked response.
    Input: valid template payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_template_payload(
        template_name="welcome", language_code="en_US"
    )
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_video_sender(mock_post, client):
    """
    Test VideoSender _send_request with valid payload and mocked response.
    Input: valid video payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_video_payload(media_id="mediaid")
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_read_mark(mock_post, client):
    """
    Test ReadMark _send_request with valid payload and mocked response.
    Input: valid read receipt payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_read_payload("msgid")
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_contextual_reply(mock_post, client):
    """
    Test ContextualReply _send_request with valid payload and mocked response.
    Input: valid contextual reply payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_contextual_reply_payload(
        reply_to_message_id="msgid", message_type="text", message_content={"body": "Hi"}
    )
    result = client._send_request(payload)
    assert result.status_code == 200


@patch("requests.post")
def test_typing_indicator(mock_post, client):
    """
    Test TypingIndicator _send_request with valid payload and mocked response.
    Input: valid typing indicator payload, mocked requests.post.
    Output: status_code 200.
    """
    mock_post.return_value.status_code = 200
    mock_post.return_value.json.return_value = {"messages": ["ok"]}
    payload = client._build_typing_indicator_payload("typing")
    result = client._send_request(payload)
    assert result.status_code == 200


def test_address_sender_payload():
    """
    Test AddressSender _build_address_payload with minimal valid input.
    Input: body, country_iso_code.
    Output: Payload contains correct WhatsApp fields and action name.
    """

    class Dummy(AddressSender):
        def __init__(self):
            self.recipient_to_send = "1234567890"

    client = Dummy()
    payload = client._build_address_payload(body="Address body", country_iso_code="IN")
    assert payload["messaging_product"] == "whatsapp"
    assert payload["interactive"]["action"]["name"] == "address_message"


def test_audio_sender_payload():
    """
    Test AudioSender _build_audio_payload with media_id.
    Input: media_id.
    Output: Payload contains 'audio' with correct 'id'.
    """

    class Dummy(AudioSender):
        def __init__(self):
            self.recipient_to_send = "1234567890"

    client = Dummy()
    payload = client._build_audio_payload(media_id="mediaid")
    assert payload["audio"]["id"] == "mediaid"


def test_base_client_init():
    """
    Test WhatsAppBaseClient initialization.
    Input: all required args.
    Output: Attributes are set correctly.
    """
    client = WhatsAppBaseClient(
        access_token="token",
        mobile_number_id="id",
        recipient_country_code="91",
        recipient_mobile_number="9876543210",
    )
    assert client.recipient_to_send == "919876543210"


def test_contact_sender_payload():
    """
    Test ContactSender _build_contact_payload with valid contact.
    Input: contacts list.
    Output: Payload contains correct contacts.
    """

    class Dummy(ContactSender):
        def __init__(self):
            self.recipient_to_send = "1234567890"

    client = Dummy()
    contacts = [{"name": {"first_name": "John"}, "phones": [{"phone": "123"}]}]
    payload = client._build_contact_payload(contacts)
    assert payload["contacts"] == contacts


def test_document_sender_payload():
    """
    Test DocumentSender _build_document_payload with media_id.
    Input: media_id.
    Output: Payload contains 'document' with correct 'id'.
    """

    class Dummy(DocumentSender):
        def __init__(self):
            self.recipient_to_send = "1234567890"

    client = Dummy()
    payload = client._build_document_payload(media_id="mediaid")
    assert payload["document"]["id"] == "mediaid"


def test_image_sender_payload():
    """
    Test ImageSender _build_image_payload with media_id.
    Input: media_id.
    Output: Payload contains 'image' with correct 'id'.
    """

    class Dummy(ImageSender):
        def __init__(self):
            self.recipient_to_send = "1234567890"

    client = Dummy()
    payload = client._build_image_payload(media_id="mediaid")
    assert payload["image"]["id"] == "mediaid"


def test_text_message_sender_payload():
    """
    Test TextMessageSender _build_text_payload with body.
    Input: body.
    Output: Payload contains 'text' with correct 'body'.
    """

    class Dummy(TextMessageSender):
        def __init__(self):
            self.recipient_to_send = "1234567890"

    client = Dummy()
    payload = client._build_text_payload("Hello!")
    assert payload["text"]["body"] == "Hello!"
