from whatsloon.cta import CTASender

class DummyClient(CTASender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_cta_payload():
    """
    Test building CTA payload with required fields only.
    Input: body_text, button_text, button_url.
    Output: Payload contains correct type and action name.
    """
    client = DummyClient()
    payload = client._build_cta_payload(
        body_text="Body", button_text="Click", button_url="http://example.com"
    )
    assert payload["type"] == "interactive"
    assert payload["interactive"]["action"]["name"] == "cta_url"

def test_build_cta_payload_with_header_footer():
    """
    Test building CTA payload with header and footer.
    Input: body_text, button_text, button_url, header, footer_text.
    Output: Payload includes header and footer fields.
    """
    client = DummyClient()
    payload = client._build_cta_payload(
        body_text="Body", button_text="Click", button_url="http://example.com",
        header={"type": "text", "text": "Header"}, footer_text="Footer"
    )
    assert payload["interactive"]["header"]["text"] == "Header"
    assert payload["interactive"]["footer"]["text"] == "Footer"

def test_build_cta_payload_missing_body():
    """
    Test error when body_text is missing.
    Input: No body_text.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_cta_payload(button_text="Click", button_url="http://example.com")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing body_text"

def test_build_cta_payload_missing_button_text():
    """
    Test error when button_text is missing.
    Input: No button_text.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_cta_payload(body_text="Body", button_url="http://example.com")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing button_text"

def test_build_cta_payload_missing_button_url():
    """
    Test error when button_url is missing.
    Input: No button_url.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_cta_payload(body_text="Body", button_text="Click")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing button_url"
