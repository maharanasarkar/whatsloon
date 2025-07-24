import pytest
from whatsloon.contact import ContactSender

class DummyClient(ContactSender):
    def __init__(self):
        self.recipient_to_send = "1234567890"
        self.base_url = "https://graph.facebook.com/v19.0/1234567890/messages"
        self.headers = {"Authorization": "Bearer testtoken"}

def test_build_contact_payload():
    """
    Test building contact payload with a valid single contact.
    Input: List with one contact dict.
    Output: Payload contains correct type and contacts list.
    """
    client = DummyClient()
    contacts = [{"name": {"first_name": "John"}, "phones": [{"phone": "123"}]}]
    payload = client._build_contact_payload(contacts)
    assert payload["type"] == "contacts"
    assert payload["contacts"] == contacts

def test_build_contact_payload_error():
    """
    Test error when contacts list is empty.
    Input: Empty list.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_contact_payload([])

def test_build_contact_payload_not_a_list():
    """
    Test error when contacts is not a list.
    Input: contacts is a dict, not a list.
    Output: Should raise ValueError.
    """
    client = DummyClient()
    with pytest.raises(ValueError):
        client._build_contact_payload({"name": {"first_name": "Jane"}})

def test_build_contact_payload_multiple_contacts():
    """
    Test building contact payload with multiple contacts.
    Input: List with two contact dicts.
    Output: Payload contains both contacts in the list.
    """
    client = DummyClient()
    contacts = [
        {"name": {"first_name": "John"}, "phones": [{"phone": "123"}]},
        {"name": {"first_name": "Jane"}, "phones": [{"phone": "456"}]}
    ]
    payload = client._build_contact_payload(contacts)
    assert payload["contacts"] == contacts
