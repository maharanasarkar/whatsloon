"""Parser, router, and filter tests over fixture envelopes."""

from pathlib import Path

import pytest

from whatsloon.exceptions import InvalidPayloadError, UnsupportedEventError
from whatsloon.webhooks.events import UnknownEvent, WebhookMessageReceived, WebhookMessageStatus
from whatsloon.webhooks.filters import SubscriptionFilter
from whatsloon.webhooks.parser import parse_body, parse_envelope
from whatsloon.webhooks.router import EventRouter

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "webhooks"


def _load(name):
    """Load a fixture envelope.

    Args:
        name: Fixture file name.

    Returns:
        Raw bytes.
    """
    return (FIXTURES / name).read_bytes()


def test_message_fixture_parses_to_received():
    """Message fixtures normalize with version stamps."""
    events = parse_body(_load("message_received.json"), api_version="v26.0")
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, WebhookMessageReceived)
    assert event.message_id == "wamid.fixture-msg-1"
    assert event.sender == "919876543210"
    assert event.text_body == "Hello!"
    assert event.api_version == "v26.0"


def test_status_fixture_parses_to_status():
    """Status fixtures normalize delivery transitions."""
    events = parse_body(_load("message_status.json"), api_version="v19.0")
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, WebhookMessageStatus)
    assert event.status == "delivered"
    assert event.api_version == "v19.0"


def test_unknown_future_preserved():
    """Unrecognized shapes survive as UnknownEvent with raw data."""
    events = parse_body(_load("unknown_future.json"))
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, UnknownEvent)
    assert event.raw["future_surface"]["never_seen_before"] is True


def test_live_fixture_parses_from_user_id():
    """Live-captured traffic exposes BSUID on the message object."""
    events = parse_body(_load("live_message_received.json"), api_version="v26.0")
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, WebhookMessageReceived)
    assert event.message_id == "wamid.live-msg-1"
    assert event.user_id == "bsuid-live-user-1"
    assert event.text_body == "Hello live!"


def test_malformed_bodies_raise():
    """Non-JSON and non-object bodies raise without event loss ambiguity."""
    with pytest.raises(InvalidPayloadError):
        parse_body(b"not json")
    with pytest.raises(InvalidPayloadError):
        parse_body(b"[1, 2]")
    assert parse_envelope({})[0].event_type == "unknown"


def test_router_dispatch_filter_and_fallback():
    """Routing honors types, filters skip, fallback catches unknown."""
    router = EventRouter()
    seen = []
    router.register("message.received", seen.append)
    router.register("message.status", seen.append, SubscriptionFilter(allow_senders={"nobody"}))
    router.set_fallback(seen.append)
    received = WebhookMessageReceived(message_id="w-1", sender="919")
    status = WebhookMessageStatus(message_id="w-2", status="read")
    unknown = UnknownEvent(reason="x", raw={})
    router.dispatch(received)
    assert router.dispatch(status) is None
    router.dispatch(unknown)
    assert [e.message_id if hasattr(e, "message_id") else "unknown" for e in seen] == [
        "w-1",
        "unknown",
    ]


def test_router_without_fallback_raises():
    """Unregistered types fail loudly without a fallback."""
    router = EventRouter()
    with pytest.raises(UnsupportedEventError):
        router.dispatch(UnknownEvent(reason="x", raw={}))


def test_filter_predicates():
    """Custom predicates compose with type rules."""
    filt = SubscriptionFilter(
        allow_types={"message.received"},
        predicate=lambda e: getattr(e, "sender", "") == "919",
    )
    assert filt.matches(WebhookMessageReceived(sender="919")) is True
    assert filt.matches(WebhookMessageReceived(sender="other")) is False
    assert filt.matches(WebhookMessageStatus()) is False
