import pytest
from whatsloon.sticker import StickerSender

class DummyClient(StickerSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_sticker_payload_media_id():
    """
    Test building sticker payload with only media_id provided.
    Input: media_id
    Output: Payload contains 'sticker' with correct 'id'.
    """
    client = DummyClient()
    payload = client._build_sticker_payload(media_id="mediaid")
    assert payload["type"] == "sticker"
    assert payload["sticker"]["id"] == "mediaid"

def test_build_sticker_payload_error():
    """
    Test error when neither media_id nor media_link is provided.
    Input: no arguments
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_sticker_payload()

def test_build_sticker_payload_media_link():
    """
    Test building sticker payload with only media_link provided.
    Input: media_link
    Output: Payload contains 'sticker' with correct 'link'.
    """
    client = DummyClient()
    payload = client._build_sticker_payload(media_link="http://example.com/sticker.webp")
    assert payload["sticker"]["link"] == "http://example.com/sticker.webp"

def test_build_sticker_payload_both_fields():
    """
    Test building sticker payload with both media_id and media_link provided.
    Input: media_id and media_link
    Output: Payload contains both 'id' and 'link' in 'sticker'.
    """
    client = DummyClient()
    payload = client._build_sticker_payload(media_id="mediaid", media_link="http://example.com/sticker.webp")
    assert payload["sticker"]["id"] == "mediaid"
    assert payload["sticker"]["link"] == "http://example.com/sticker.webp"

def test_build_sticker_payload_empty_media_id():
    """
    Test error when media_id is empty string and no media_link.
    Input: media_id=""
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_sticker_payload(media_id="")

def test_build_sticker_payload_empty_media_link():
    """
    Test error when media_link is empty string and no media_id.
    Input: media_link=""
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_sticker_payload(media_link="")
