from whatsloon.template import TemplateSender

class DummyClient(TemplateSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_template_payload():
    """
    Test building template payload with required fields only.
    Input: template_name, language_code.
    Output: Payload contains correct WhatsApp fields and template data.
    """
    client = DummyClient()
    payload = client._build_template_payload(
        template_name="welcome", language_code="en_US"
    )
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "template"
    assert payload["template"]["name"] == "welcome"
    assert payload["template"]["language"]["code"] == "en_US"

def test_build_template_payload_with_components():
    """
    Test building template payload with components.
    Input: template_name, language_code, components.
    Output: Payload includes components in template.
    """
    client = DummyClient()
    components = [{"type": "body", "parameters": [{"type": "text", "text": "Hello"}]}]
    payload = client._build_template_payload(
        template_name="welcome", language_code="en_US", components=components
    )
    assert payload["template"]["components"] == components

def test_build_template_payload_with_recipient_type():
    """
    Test building template payload with recipient_type.
    Input: template_name, language_code, recipient_type="group".
    Output: Payload includes recipient_type as 'group'.
    """
    client = DummyClient()
    payload = client._build_template_payload(
        template_name="welcome", language_code="en_US", recipient_type="group"
    )
    assert payload["recipient_type"] == "group"

def test_build_template_payload_missing_template_name():
    """
    Test error when template_name is missing.
    Input: No template_name.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_template_payload(language_code="en_US")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing template_name"

def test_build_template_payload_missing_language_code():
    """
    Test error when language_code is missing.
    Input: No language_code.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_template_payload(template_name="welcome")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing language_code"
