from whatsloon.flow import FlowSender

class DummyClient(FlowSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_flow_payload():
    """
    Test building flow payload with required fields only.
    Input: flow_token, flow_id, flow_cta, flow_action.
    Output: Payload contains correct WhatsApp fields and flow action name.
    """
    client = DummyClient()
    payload = client._build_flow_payload(
        flow_token="token", flow_id="id", flow_cta="cta", flow_action="navigate"
    )
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "interactive"
    assert payload["interactive"]["action"]["name"] == "flow"

def test_build_flow_payload_with_all_fields():
    """
    Test building flow payload with all optional fields.
    Input: All required and optional fields.
    Output: Payload includes header, body, footer, and flow_action_payload.
    """
    client = DummyClient()
    payload = client._build_flow_payload(
        flow_token="token", flow_id="id", flow_cta="cta", flow_action="navigate",
        flow_message_version="4", body_text="Body", header={"type": "text", "text": "Header"},
        footer_text="Footer", flow_action_payload={"key": "value"}
    )
    assert payload["interactive"]["header"]["text"] == "Header"
    assert payload["interactive"]["body"]["text"] == "Body"
    assert payload["interactive"]["footer"]["text"] == "Footer"
    assert payload["interactive"]["action"]["parameters"]["key"] == "value"

def test_build_flow_payload_missing_token():
    """
    Test error when flow_token is missing.
    Input: No flow_token.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_flow_payload(flow_id="id", flow_cta="cta", flow_action="navigate")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing flow_token"

def test_build_flow_payload_missing_flow_id():
    """
    Test error when flow_id is missing.
    Input: No flow_id.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_flow_payload(flow_token="token", flow_cta="cta", flow_action="navigate")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing flow_id"

def test_build_flow_payload_missing_cta():
    """
    Test error when flow_cta is missing.
    Input: No flow_cta.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_flow_payload(flow_token="token", flow_id="id", flow_action="navigate")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing flow_cta"

def test_build_flow_payload_missing_action():
    """
    Test error when flow_action is missing.
    Input: No flow_action.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    try:
        client._build_flow_payload(flow_token="token", flow_id="id", flow_cta="cta")
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing flow_action"
