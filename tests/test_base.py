import pytest
from whatsloon.base import WhatsAppBaseClient

def test_valid_initialization():
    """
    Test valid initialization with all required arguments.
    Input: All valid arguments provided.
    Output: Attributes are set correctly, recipient_to_send is country code + mobile number.
    """
    client = WhatsAppBaseClient(
        access_token="token",
        phone_number_id="1234567890",
        recipient_mobile_number="9876543210",
        recipient_country_code="91",
        api_version="v19.0"
    )
    assert client.recipient_to_send == "919876543210"
    assert client.base_url.endswith("/1234567890/messages")
    assert client.headers["Authorization"] == "Bearer token"

def test_valid_initialization_with_plus():
    """
    Test valid initialization with plus sign in country code and mobile number.
    Input: recipient_country_code and recipient_mobile_number with leading '+'.
    Output: recipient_to_send is normalized to digits only, no plus sign.
    """
    client = WhatsAppBaseClient(
        access_token="token",
        phone_number_id="1234567890",
        recipient_mobile_number="+9876543210",
        recipient_country_code="+91",
        api_version="v19.0"
    )
    assert client.recipient_to_send == "919876543210"

def test_valid_initialization_no_country_code():
    """
    Test valid initialization without country code.
    Input: Only mobile number provided, no country code.
    Output: recipient_to_send equals mobile number only.
    """
    client = WhatsAppBaseClient(
        access_token="token",
        phone_number_id="1234567890",
        recipient_mobile_number="9876543210",
        api_version="v19.0"
    )
    assert client.recipient_to_send == "9876543210"

def test_invalid_access_token():
    """
    Test invalid access_token (empty string).
    Input: access_token is empty.
    Output: Raises ValueError.
    """
    with pytest.raises(ValueError):
        WhatsAppBaseClient(
            access_token=" ",
            phone_number_id="1234567890",
            recipient_mobile_number="9876543210"
        )

def test_invalid_phone_number_id():
    """
    Test invalid phone_number_id (empty string).
    Input: phone_number_id is empty.
    Output: Raises ValueError.
    """
    with pytest.raises(ValueError):
        WhatsAppBaseClient(
            access_token="token",
            phone_number_id=" ",
            recipient_mobile_number="9876543210"
        )

def test_invalid_mobile_number_type():
    """
    Test invalid mobile number (not digits).
    Input: recipient_mobile_number is not numeric.
    Output: Raises ValueError.
    """
    with pytest.raises(ValueError):
        WhatsAppBaseClient(
            access_token="token",
            phone_number_id="1234567890",
            recipient_mobile_number="notanumber"
        )

def test_invalid_mobile_number_length():
    """
    Test invalid mobile number (too short).
    Input: recipient_mobile_number is less than 6 digits.
    Output: Raises ValueError.
    """
    with pytest.raises(ValueError):
        WhatsAppBaseClient(
            access_token="token",
            phone_number_id="1234567890",
            recipient_mobile_number="123"
        )

def test_invalid_country_code_type():
    """
    Test invalid country code type (not a string).
    Input: recipient_country_code is not a string.
    Output: Raises TypeError.
    """
    with pytest.raises(TypeError):
        WhatsAppBaseClient(
            access_token="token",
            phone_number_id="1234567890",
            recipient_mobile_number="9876543210",
            recipient_country_code=123
        )

def test_invalid_country_code_format():
    """
    Test invalid country code format (not digits).
    Input: recipient_country_code is not numeric.
    Output: Raises ValueError.
    """
    with pytest.raises(ValueError):
        WhatsAppBaseClient(
            access_token="token",
            phone_number_id="1234567890",
            recipient_mobile_number="9876543210",
            recipient_country_code="abc"
        )

def test_invalid_api_version():
    """
    Test invalid api_version (empty string).
    Input: api_version is empty.
    Output: Raises ValueError.
    """
    with pytest.raises(ValueError):
        WhatsAppBaseClient(
            access_token="token",
            phone_number_id="1234567890",
            recipient_mobile_number="9876543210",
            api_version=" "
        )

def test_base_client_init():
    """
    Test normal initialization of WhatsAppBaseClient.
    Input: All required arguments provided.
    Output: Attributes are set correctly.
    """
    client = WhatsAppBaseClient(
        access_token="token",
        phone_number_id="id",
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
            phone_number_id="id",
            recipient_country_code="91",
            recipient_mobile_number="9876543210",
        )
    except TypeError:
        pass
    else:
        assert False, "TypeError not raised for missing access_token"

def test_base_client_missing_phone_number_id():
    """
    Test missing phone_number_id argument.
    Input: No phone_number_id.
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
        assert False, "TypeError not raised for missing phone_number_id"

def test_base_client_invalid_country_code():
    """
    Test invalid country code (non-numeric).
    Input: recipient_country_code="XX"
    Output: recipient_to_send should still concatenate, but not be a valid phone number.
    """
    try:
        client = WhatsAppBaseClient(
            access_token="token",
            phone_number_id="id",
            recipient_country_code="XX",
            recipient_mobile_number="9876543210",
        )
        assert client.recipient_to_send == "XX9876543210"
    except ValueError:
        pass


def test_base_client_none_country_code():
    """
    Test None as country code.
    Input: recipient_country_code=None
    Output: recipient_to_send should equal mobile number only.
    """
    client = WhatsAppBaseClient(
        access_token="token",
        phone_number_id="id",
        recipient_country_code=None,
        recipient_mobile_number="9876543210",
    )
    assert client.recipient_to_send == "9876543210"
