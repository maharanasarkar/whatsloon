import pytest
from whatsloon.text import TextMessageSender


class DummyClient(TextMessageSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {
            "Authorization": "Bearer testtoken",
            "Content-Type": "application/json",
        }


def test_build_text_payload():
    """
    Test building text payload with preview_url False.
    Input: body, preview_url=False.
    Output: Payload contains correct WhatsApp fields and preview_url is False.
    """
    client = DummyClient()
    payload = client._build_text_payload("Hello, world!", preview_url=False)
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "text"
    assert payload["text"]["body"] == "Hello, world!"
    assert payload["text"]["preview_url"] is False

def test_build_text_payload_preview_url_true():
    """
    Test building text payload with preview_url True.
    Input: body, preview_url=True.
    Output: Payload contains preview_url True.
    """
    client = DummyClient()
    payload = client._build_text_payload("Hi there!", preview_url=True)
    assert payload["text"]["preview_url"] is True


def test_send_text_message_success(monkeypatch):
    """
    Test send_text_message returns success on valid response.
    Input: message, preview_url=True, mocked _send_request.
    Output: Result dict with success True and data.
    """
    client = DummyClient()

    class DummyResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"messages": ["sent"]}

    def dummy_post(*args, **kwargs):
        return DummyResponse()

    monkeypatch.setattr(client, "_send_request", lambda payload: dummy_post())
    result = client.send_text_message("Test message", preview_url=True)
    assert result["success"] is True
    assert "data" in result


def test_send_text_message_http_error(monkeypatch):
    """
    Test send_text_message returns error on HTTP error.
    Input: message, preview_url=True, mocked _send_request raises HTTPError.
    Output: Result dict with success False and error.
    """
    client = DummyClient()

    class DummyHTTPError(Exception):
        def __init__(self):
            self.response = type("r", (), {"status_code": 400, "text": "Bad Request"})()

    def dummy_post(*args, **kwargs):
        raise DummyHTTPError()

    monkeypatch.setattr(client, "_send_request", lambda payload: dummy_post())
    result = client.send_text_message("Test message", preview_url=True)
    assert result["success"] is False
    assert "error" in result


def test_send_text_message_exception(monkeypatch):
    """
    Test send_text_message returns error on generic exception.
    Input: message, preview_url=True, mocked _send_request raises Exception.
    Output: Result dict with success False and error message.
    """
    client = DummyClient()
    monkeypatch.setattr(
        client,
        "_send_request",
        lambda payload: (_ for _ in ()).throw(Exception("fail")),
    )
    result = client.send_text_message("Test message", preview_url=True)
    assert result["success"] is False
    assert result["error"] == "fail"

def test_build_text_payload_missing_body():
    """
    Test error when body is missing.
    Input: preview_url provided, no body.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    with pytest.raises(TypeError):
        client._build_text_payload(preview_url=True)
