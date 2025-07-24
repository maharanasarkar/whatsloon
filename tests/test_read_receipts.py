from whatsloon.read_receipts import ReadMark

class DummyClient(ReadMark):
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_read_payload():
    """
    Test building read receipt payload with valid message_id.
    Input: message_id string.
    Output: Payload contains correct WhatsApp fields and status.
    """
    client = DummyClient()
    payload = client._build_read_payload("msgid")
    assert payload["messaging_product"] == "whatsapp"
    assert payload["status"] == "read"
    assert payload["message_id"] == "msgid"

def test_build_read_payload_missing_message_id():
    """
    Test error when message_id is missing.
    Input: No message_id argument.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_read_payload()
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing message_id"

def test_build_read_payload_empty_message_id():
    """
    Test building read receipt payload with empty message_id string.
    Input: message_id=""
    Output: Payload includes empty message_id.
    """
    client = DummyClient()
    payload = client._build_read_payload("")
    assert payload["message_id"] == ""
