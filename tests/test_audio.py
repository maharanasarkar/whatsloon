import pytest
from whatsloon.audio import AudioSender

class DummyClient(AudioSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_audio_payload_media_id():
    """
    Test building audio payload with only media_id provided.
    Input: media_id
    Output: Payload contains 'audio' with correct 'id'.
    """
    client = DummyClient()
    payload = client._build_audio_payload(media_id="mediaid")
    assert payload["type"] == "audio"
    assert payload["audio"]["id"] == "mediaid"

def test_build_audio_payload_media_link():
    """
    Test building audio payload with only media_link provided.
    Input: media_link
    Output: Payload contains 'audio' with correct 'link'.
    """
    client = DummyClient()
    payload = client._build_audio_payload(media_link="http://example.com/audio.mp3")
    assert payload["audio"]["link"] == "http://example.com/audio.mp3"

def test_build_audio_payload_error():
    """
    Test error when neither media_id nor media_link is provided.
    Input: no arguments
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_audio_payload()

def test_build_audio_payload_both_fields():
    """
    Test building audio payload with both media_id and media_link provided.
    Input: media_id and media_link
    Output: Payload contains both 'id' and 'link' in 'audio'.
    """
    client = DummyClient()
    payload = client._build_audio_payload(media_id="mediaid", media_link="http://example.com/audio.mp3")
    assert payload["audio"]["id"] == "mediaid"
    assert payload["audio"]["link"] == "http://example.com/audio.mp3"

def test_build_audio_payload_empty_media_id():
    """
    Test error when media_id is empty string and no media_link.
    Input: media_id=""
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_audio_payload(media_id="")

def test_build_audio_payload_empty_media_link():
    """
    Test error when media_link is empty string and no media_id.
    Input: media_link=""
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_audio_payload(media_link="")
