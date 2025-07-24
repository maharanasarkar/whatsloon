import pytest
from whatsloon.list import ListSender

class DummyClient(ListSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_list_payload():
    """
    Test building list payload with required fields only.
    Input: body_text, button_text, sections (1 section, 1 row).
    Output: Payload contains correct WhatsApp fields and interactive type.
    """
    client = DummyClient()
    payload = client._build_list_payload(
        body_text="Choose one", button_text="Pick", sections=[{"title": "A", "rows": [{"id": "1", "title": "Row1"}]}]
    )
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "interactive"
    assert payload["interactive"]["type"] == "list"

def test_build_list_payload_button_text_limit():
    """
    Test error when button_text exceeds 20 characters.
    Input: button_text is 21 characters.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_list_payload(
            body_text="Choose one", button_text="x"*21, sections=[{"title": "A", "rows": [{"id": "1", "title": "Row1"}]}]
        )

def test_build_list_payload_section_limit():
    """
    Test error when sections exceed 10.
    Input: 11 sections.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_list_payload(
            body_text="Choose one", button_text="Pick",
            sections=[{"title": str(i), "rows": [{"id": str(i), "title": "Row"+str(i)}]} for i in range(11)]
        )

def test_build_list_payload_row_limit():
    """
    Test error when total rows exceed 10.
    Input: 2 sections, 6 rows each (12 rows total).
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_list_payload(
            body_text="Choose one", button_text="Pick",
            sections=[{"title": "A", "rows": [{"id": str(i), "title": "Row"+str(i)} for i in range(6)]},
                      {"title": "B", "rows": [{"id": str(i+6), "title": "Row"+str(i+6)} for i in range(6)]}]
        )

def test_build_list_payload_with_header_footer():
    """
    Test building list payload with header and footer.
    Input: header and footer_text provided.
    Output: Payload includes header and footer fields.
    """
    client = DummyClient()
    payload = client._build_list_payload(
        body_text="Choose one", button_text="Pick",
        sections=[{"title": "A", "rows": [{"id": "1", "title": "Row1"}]}],
        header={"type": "text", "text": "Header"}, footer_text="Footer"
    )
    assert payload["interactive"]["header"]["text"] == "Header"
    assert payload["interactive"]["footer"]["text"] == "Footer"
