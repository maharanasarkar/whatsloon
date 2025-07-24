from whatsloon.base import WhatsAppBaseClient

def test_base_client_init():
    """
    Test normal initialization of WhatsAppBaseClient.
    Input: All required arguments provided.
    Output: Attributes are set correctly.
    """
    client = WhatsAppBaseClient(
        access_token="token",
        mobile_number_id="id",
        recipient_country_code="91",
        recipient_mobile_number="9876543210",
    )
    assert client.recipient_to_send == "919876543210"
    assert client.base_url.startswith("https://graph.facebook.com/")
    assert "Authorization" in client.headers

def test_base_client_missing_token():
    """
    Test missing access_token argument.
    Input: No access_token.
    Output: Should raise TypeError.
    """
    try:
        WhatsAppBaseClient(
            mobile_number_id="id",
            recipient_country_code="91",
            recipient_mobile_number="9876543210",
        )
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing access_token"

def test_base_client_missing_mobile_number_id():
    """
    Test missing mobile_number_id argument.
    Input: No mobile_number_id.
    Output: Should raise TypeError.
    """
    try:
        WhatsAppBaseClient(
            access_token="token",
            recipient_country_code="91",
            recipient_mobile_number="9876543210",
        )
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing mobile_number_id"

def test_base_client_invalid_country_code():
    """
    Test invalid country code (non-numeric).
    Input: recipient_country_code="XX"
    Output: recipient_to_send should still concatenate, but not be a valid phone number.
    """
    client = WhatsAppBaseClient(
        access_token="token",
        mobile_number_id="id",
        recipient_country_code="XX",
        recipient_mobile_number="9876543210",
    )
    assert client.recipient_to_send == "XX9876543210"
