import pytest
from whatsloon.document import DocumentSender

class DummyClient(DocumentSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_document_payload_media_id():
    """
    Test building document payload with only media_id provided.
    Input: media_id
    Output: Payload contains 'document' with correct 'id'.
    """
    client = DummyClient()
    payload = client._build_document_payload(media_id="mediaid")
    assert payload["type"] == "document"
    assert payload["document"]["id"] == "mediaid"

def test_build_document_payload_media_link():
    """
    Test building document payload with only media_link provided.
    Input: media_link
    Output: Payload contains 'document' with correct 'link'.
    """
    client = DummyClient()
    payload = client._build_document_payload(media_link="http://example.com/doc.pdf")
    assert payload["document"]["link"] == "http://example.com/doc.pdf"

def test_build_document_payload_error():
    """
    Test error when neither media_id nor media_link is provided.
    Input: no arguments
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_document_payload()

def test_build_document_payload_both_fields():
    """
    Test building document payload with both media_id and media_link provided.
    Input: media_id and media_link
    Output: Payload contains both 'id' and 'link' in 'document'.
    """
    client = DummyClient()
    payload = client._build_document_payload(media_id="mediaid", media_link="http://example.com/doc.pdf")
    assert payload["document"]["id"] == "mediaid"
    assert payload["document"]["link"] == "http://example.com/doc.pdf"

def test_build_document_payload_with_caption_and_filename():
    """
    Test building document payload with caption and filename.
    Input: media_id, caption, filename
    Output: Payload contains caption and filename in 'document'.
    """
    client = DummyClient()
    payload = client._build_document_payload(media_id="mediaid", caption="My Doc", filename="file.pdf")
    assert payload["document"]["caption"] == "My Doc"
    assert payload["document"]["filename"] == "file.pdf"

def test_build_document_payload_empty_media_id():
    """
    Test error when media_id is empty string and no media_link.
    Input: media_id=""
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_document_payload(media_id="")

def test_build_document_payload_empty_media_link():
    """
    Test error when media_link is empty string and no media_id.
    Input: media_link=""
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_document_payload(media_link="")
