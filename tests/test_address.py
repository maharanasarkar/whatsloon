import pytest
from whatsloon.address import AddressSender

class DummyClient(AddressSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_address_payload():
    """
    Test minimal valid address payload.
    Input: body and country_iso_code only.
    Output: Payload contains correct WhatsApp fields and action name.
    """
    client = DummyClient()
    payload = client._build_address_payload(
        body="Address body", country_iso_code="IN"
    )
    assert payload["messaging_product"] == "whatsapp"
    assert payload["to"] == "1234567890"
    assert payload["type"] == "interactive"
    assert payload["interactive"]["action"]["name"] == "address_message"


def test_build_address_payload_with_all_fields():
    """
    Test address payload with all optional fields.
    Input: body, country_iso_code, header, footer, values, validation_errors, saved_addresses.
    Output: All fields present in payload and correctly mapped.
    """
    client = DummyClient()
    payload = client._build_address_payload(
        body="Full address",
        country_iso_code="US",
        header="Header text",
        footer="Footer text",
        values={"name": "John", "phone_number": "555-1234", "address": "123 Main St"},
        validation_errors={"in_pin_code": "Invalid pin code"},
        saved_addresses=[{"id": "1", "address": "Old Address"}]
    )
    assert payload["interactive"]["header"] == {"type": "text", "text": "Header text"}
    assert payload["interactive"]["footer"] == {"text": "Footer text"}
    params = payload["interactive"]["action"]["parameters"]
    assert params["country"] == "US"
    assert params["values"]["name"] == "John"
    assert params["validation_errors"]["in_pin_code"] == "Invalid pin code"
    assert params["saved_addresses"][0]["address"] == "Old Address"

def test_build_address_payload_missing_body():
    """
    Test missing required 'body' argument.
    Input: Only country_iso_code provided.
    Output: Should raise TypeError due to missing required argument.
    """
    client = DummyClient()
    with pytest.raises(TypeError):
        client._build_address_payload(country_iso_code="IN")

def test_build_address_payload_missing_country():
    """
    Test missing required 'country_iso_code' argument.
    Input: Only body provided.
    Output: Should raise TypeError due to missing required argument.
    """
    client = DummyClient()
    with pytest.raises(TypeError):
        client._build_address_payload(body="Address body")

def test_build_address_payload_empty_values():
    """
    Test empty values dict.
    Input: values is an empty dict.
    Output: 'values' should not appear in parameters of payload.
    """
    client = DummyClient()
    payload = client._build_address_payload(body="Body", country_iso_code="IN", values={})
    assert "values" not in payload["interactive"]["action"]["parameters"]

def test_build_address_payload_empty_saved_addresses():
    """
    Test empty saved_addresses list.
    Input: saved_addresses is an empty list.
    Output: 'saved_addresses' should not appear in parameters of payload.
    """
    client = DummyClient()
    payload = client._build_address_payload(body="Body", country_iso_code="IN", saved_addresses=[])
    assert "saved_addresses" not in payload["interactive"]["action"]["parameters"]
