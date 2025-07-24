import pytest
from whatsloon.video import VideoSender

class DummyClient(VideoSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_video_payload_media_id():
    """
    Test building video payload with only media_id provided.
    Input: media_id
    Output: Payload contains 'video' with correct 'id'.
    """
    client = DummyClient()
    payload = client._build_video_payload(media_id="mediaid")
    assert payload["type"] == "video"
    assert payload["video"]["id"] == "mediaid"

def test_build_video_payload_media_link():
    """
    Test building video payload with only media_link provided.
    Input: media_link
    Output: Payload contains 'video' with correct 'link'.
    """
    client = DummyClient()
    payload = client._build_video_payload(media_link="http://example.com/vid.mp4")
    assert payload["video"]["link"] == "http://example.com/vid.mp4"

def test_build_video_payload_error():
    """
    Test error when neither media_id nor media_link is provided.
    Input: no arguments
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_video_payload()

def test_build_video_payload_both_fields():
    """
    Test building video payload with both media_id and media_link provided.
    Input: media_id and media_link
    Output: Payload contains both 'id' and 'link' in 'video'.
    """
    client = DummyClient()
    payload = client._build_video_payload(media_id="mediaid", media_link="http://example.com/vid.mp4")
    assert payload["video"]["id"] == "mediaid"
    assert payload["video"]["link"] == "http://example.com/vid.mp4"

def test_build_video_payload_with_caption():
    """
    Test building video payload with caption.
    Input: media_id and caption.
    Output: Payload contains caption in 'video'.
    """
    client = DummyClient()
    payload = client._build_video_payload(media_id="mediaid", caption="A video")
    assert payload["video"]["caption"] == "A video"

def test_build_video_payload_empty_media_id():
    """
    Test error when media_id is empty string and no media_link.
    Input: media_id=""
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_video_payload(media_id="")

def test_build_video_payload_empty_media_link():
    """
    Test error when media_link is empty string and no media_id.
    Input: media_link=""
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_video_payload(media_link="")
