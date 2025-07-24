from whatsloon.contextual_reply import ContextualReply

class DummyClient(ContextualReply):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_contextual_reply_payload():
    """
    Test building contextual reply payload with valid text message.
    Input: reply_to_message_id, message_type, message_content.
    Output: Payload contains correct WhatsApp fields and context.
    """
    client = DummyClient()
    payload = client._build_contextual_reply_payload(
        reply_to_message_id="msgid", message_type="text", message_content={"body": "Hi"}
    )
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "text"
    assert payload["context"]["message_id"] == "msgid"
    assert payload["text"]["body"] == "Hi"

def test_build_contextual_reply_payload_different_type():
    """
    Test building contextual reply payload with image message type.
    Input: reply_to_message_id, message_type='image', message_content with id.
    Output: Payload contains correct type and image id.
    """
    client = DummyClient()
    payload = client._build_contextual_reply_payload(
        reply_to_message_id="msgid2", message_type="image", message_content={"id": "img123"}
    )
    assert payload["type"] == "image"
    assert payload["context"]["message_id"] == "msgid2"
    assert payload["image"]["id"] == "img123"

def test_build_contextual_reply_payload_missing_message_id():
    """
    Test error when reply_to_message_id is missing (None).
    Input: reply_to_message_id=None.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_contextual_reply_payload(
            reply_to_message_id=None, message_type="text", message_content={"body": "Hi"}
        )
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing reply_to_message_id"

def test_build_contextual_reply_payload_missing_message_type():
    """
    Test error when message_type is missing (None).
    Input: message_type=None.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_contextual_reply_payload(
            reply_to_message_id="msgid", message_type=None, message_content={"body": "Hi"}
        )
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing message_type"

def test_build_contextual_reply_payload_empty_message_content():
    """
    Test building contextual reply payload with empty message_content.
    Input: message_content is empty dict.
    Output: Payload still includes type and context, but message_type key is empty dict.
    """
    client = DummyClient()
    payload = client._build_contextual_reply_payload(
        reply_to_message_id="msgid", message_type="text", message_content={}
    )
    assert payload["type"] == "text"
    assert payload["text"] == {}
