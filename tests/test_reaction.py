from whatsloon.reaction import ReactionSender

class DummyClient(ReactionSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_reaction_payload():
    """
    Test building reaction payload with valid message_id and emoji.
    Input: message_id, emoji.
    Output: Payload contains correct WhatsApp fields and reaction data.
    """
    client = DummyClient()
    payload = client._build_reaction_payload("msgid", "😀")
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "reaction"
    assert payload["reaction"]["message_id"] == "msgid"
    assert payload["reaction"]["emoji"] == "😀"

def test_build_reaction_payload_missing_message_id():
    """
    Test error when message_id is missing.
    Input: No message_id.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_reaction_payload(emoji="😀")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing message_id"

def test_build_reaction_payload_missing_emoji():
    """
    Test error when emoji is missing.
    Input: No emoji.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_reaction_payload("msgid")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing emoji"

def test_build_reaction_payload_empty_emoji():
    """
    Test building reaction payload with empty emoji string.
    Input: message_id, emoji=""
    Output: Payload includes empty emoji.
    """
    client = DummyClient()
    payload = client._build_reaction_payload("msgid", "")
    assert payload["reaction"]["emoji"] == ""
