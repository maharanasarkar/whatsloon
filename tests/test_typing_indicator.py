from whatsloon.typing_indicator import TypingIndicator

class DummyClient(TypingIndicator):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_typing_indicator_payload():
    """
    Test building typing indicator payload with status 'typing'.
    Input: status='typing'.
    Output: Payload contains correct WhatsApp fields and status.
    """
    client = DummyClient()
    payload = client._build_typing_indicator_payload("typing")
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "typing"
    assert payload["typing"]["status"] == "typing"

def test_build_typing_indicator_payload_paused():
    """
    Test building typing indicator payload with status 'paused'.
    Input: status='paused'.
    Output: Payload contains status 'paused'.
    """
    client = DummyClient()
    payload = client._build_typing_indicator_payload("paused")
    assert payload["typing"]["status"] == "paused"

def test_build_typing_indicator_payload_invalid_status():
    """
    Test error when status is invalid.
    Input: status='invalid'.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    try:
        client._build_typing_indicator_payload("invalid")
    except ValueError:
        pass
    else:
        assert False, "ValueError not raised for invalid status"
