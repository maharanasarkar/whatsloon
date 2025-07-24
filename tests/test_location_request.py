from whatsloon.location_request import LocationRequestSender

class DummyClient(LocationRequestSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_location_request_payload():
    """
    Test building location request payload with valid body_text.
    Input: body_text string.
    Output: Payload contains correct WhatsApp fields and interactive type.
    """
    client = DummyClient()
    payload = client._build_location_request_payload("Share location?")
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "interactive"
    assert payload["interactive"]["type"] == "location_request_message"

def test_build_location_request_payload_empty_body():
    """
    Test building location request payload with empty body_text.
    Input: body_text is empty string.
    Output: Payload still includes interactive type and empty text.
    """
    client = DummyClient()
    payload = client._build_location_request_payload("")
    assert payload["interactive"]["body"]["text"] == ""

def test_build_location_request_payload_missing_body():
    """
    Test error when body_text is missing.
    Input: No body_text argument.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_location_request_payload()
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing body_text"
