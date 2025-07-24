import pytest
from whatsloon.reply_buttons import ReplyButtonSender

class DummyClient(ReplyButtonSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_reply_buttons_payload():
    """
    Test building reply buttons payload with valid input.
    Input: body_text, 1 button.
    Output: Payload contains correct WhatsApp fields and interactive type.
    """
    client = DummyClient()
    payload = client._build_reply_buttons_payload(
        body_text="Reply?", buttons=[{"type": "reply", "reply": {"id": "1", "title": "Yes"}}]
    )
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "interactive"
    assert payload["interactive"]["type"] == "button"

def test_build_reply_buttons_payload_button_limit():
    """
    Test error when more than 3 buttons are provided.
    Input: 4 buttons.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_reply_buttons_payload(
            body_text="Reply?", buttons=[{"type": "reply", "reply": {"id": str(i), "title": "Btn"}} for i in range(4)]
        )

def test_build_reply_buttons_payload_title_length():
    """
    Test error when a button title exceeds 20 characters.
    Input: 1 button with title length 21.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_reply_buttons_payload(
            body_text="Reply?", buttons=[{"type": "reply", "reply": {"id": "1", "title": "x"*21}}]
        )

def test_build_reply_buttons_payload_invalid_header_type():
    """
    Test error when header type is invalid.
    Input: header type is 'audio'.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_reply_buttons_payload(
            body_text="Reply?", buttons=[{"type": "reply", "reply": {"id": "1", "title": "Yes"}}],
            header={"type": "audio", "audio": {"id": "123"}}
        )

def test_build_reply_buttons_payload_with_header_footer():
    """
    Test building reply buttons payload with valid header and footer.
    Input: header (text), footer_text.
    Output: Payload includes header and footer fields.
    """
    client = DummyClient()
    payload = client._build_reply_buttons_payload(
        body_text="Reply?", buttons=[{"type": "reply", "reply": {"id": "1", "title": "Yes"}}],
        header={"type": "text", "text": "Header"}, footer_text="Footer"
    )
    assert payload["interactive"]["header"]["text"] == "Header"
    assert payload["interactive"]["footer"]["text"] == "Footer"
