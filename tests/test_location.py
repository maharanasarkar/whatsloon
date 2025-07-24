import pytest
from whatsloon.location import LocationSender

class DummyClient(LocationSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_location_payload():
    """
    Test building location payload with all fields.
    Input: latitude, longitude, name, address.
    Output: Payload contains correct type and all location fields.
    """
    client = DummyClient()
    payload = client._build_location_payload(37.7749, -122.4194, name="SF", address="CA")
    assert payload["type"] == "location"
    assert payload["location"]["latitude"] == 37.7749
    assert payload["location"]["longitude"] == -122.4194
    assert payload["location"]["name"] == "SF"
    assert payload["location"]["address"] == "CA"

def test_build_location_payload_latitude_error():
    """
    Test error when latitude is out of range.
    Input: latitude=100 (invalid), longitude=0.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_location_payload(100, 0)

def test_build_location_payload_longitude_error():
    """
    Test error when longitude is out of range.
    Input: latitude=0, longitude=200 (invalid).
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_location_payload(0, 200)

def test_build_location_payload_minimal():
    """
    Test building location payload with only required fields.
    Input: latitude, longitude.
    Output: Payload contains type and location with lat/lon only.
    """
    client = DummyClient()
    payload = client._build_location_payload(12.34, 56.78)
    assert payload["type"] == "location"
    assert payload["location"]["latitude"] == 12.34
    assert payload["location"]["longitude"] == 56.78
    assert "name" not in payload["location"]
    assert "address" not in payload["location"]

def test_build_location_payload_missing_latitude():
    """
    Test error when latitude is missing.
    Input: Only longitude provided.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    with pytest.raises(TypeError):
        client._build_location_payload(longitude=56.78)

def test_build_location_payload_missing_longitude():
    """
    Test error when longitude is missing.
    Input: Only latitude provided.
    Output: Should raise TypeError.
    """
    client = DummyClient()
    with pytest.raises(TypeError):
        client._build_location_payload(12.34)
