"""Verifier and event tests with known-answer vectors."""

import pytest

from whatsloon.exceptions import ConfigurationError, InvalidPayloadError, InvalidSignatureError
from whatsloon.webhooks.events import UnknownEvent, WebhookMessageReceived, WebhookMessageStatus
from whatsloon.webhooks.verifier import compute_signature, verify_handshake, verify_signature

SECRET = "test-app-secret"
BODY = b'{"object":"whatsapp_business_account","entry":[]}'


def test_known_answer_signature():
    """Signature computation matches an independent HMAC calculation."""
    import hashlib
    import hmac

    expected = "sha256=" + hmac.new(SECRET.encode(), BODY, hashlib.sha256).hexdigest()
    assert compute_signature(SECRET, BODY) == expected
    verify_signature(SECRET, BODY, expected)


def test_tampered_body_rejected():
    """Any byte change fails verification."""
    header = compute_signature(SECRET, BODY)
    with pytest.raises(InvalidSignatureError):
        verify_signature(SECRET, BODY + b" ", header)


def test_wrong_secret_rejected():
    """Mismatched secrets fail closed."""
    header = compute_signature(SECRET, BODY)
    with pytest.raises(InvalidSignatureError):
        verify_signature("other-secret", BODY, header)


def test_missing_secret_or_header_fails_closed():
    """Absent secret or header never passes."""
    with pytest.raises(ConfigurationError):
        verify_signature(None, BODY, compute_signature(SECRET, BODY))
    with pytest.raises(InvalidSignatureError):
        verify_signature(SECRET, BODY, None)
    with pytest.raises(InvalidSignatureError):
        verify_signature(SECRET, BODY, "md5=deadbeef")


def test_handshake_challenge_flow():
    """Matching tokens echo the challenge; mismatches raise."""
    assert (
        verify_handshake(
            mode="subscribe",
            verify_token_expected="tok",
            verify_token_received="tok",
            challenge="ch-1",
        )
        == "ch-1"
    )
    with pytest.raises(InvalidPayloadError):
        verify_handshake(
            mode="subscribe",
            verify_token_expected="tok",
            verify_token_received="wrong",
            challenge="ch-1",
        )
    with pytest.raises(InvalidPayloadError):
        verify_handshake(
            mode="unsubscribe",
            verify_token_expected="tok",
            verify_token_received="tok",
            challenge="ch-1",
        )


def test_event_models_preserve_raw():
    """Normalized events keep raw content for later handling."""
    received = WebhookMessageReceived(message_id="w-1", raw={"id": "w-1", "future": 1})
    assert received.event_type == "message.received"
    assert received.raw["future"] == 1
    assert WebhookMessageStatus(message_id="w-2", status="read").event_type == "message.status"
    unknown = UnknownEvent(reason="no value", raw={"a": 1})
    assert unknown.raw == {"a": 1}
