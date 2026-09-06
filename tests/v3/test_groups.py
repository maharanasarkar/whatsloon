"""Group service and extended webhook coverage tests."""

import httpx

from whatsloon.config.settings import RetryConfig, TimeoutConfig
from whatsloon.groups.models import GroupCreate
from whatsloon.groups.service import GroupService
from whatsloon.messages.models import OutboundMessage, PinMessage, TextMessage
from whatsloon.messages.serializers import serialize_envelope
from whatsloon.transport.sync import SyncTransport
from whatsloon.webhooks.events import WebhookCallEvent
from whatsloon.webhooks.parser import parse_body

GROUP_ID = "Y2FwaV9ncm91cDoxNzA1NTU1MDEzOToxMjAzNjM0MDQ2OTQyMzM4MjAZD"


def _service(monkeypatch, routes):
    """Build a group service over mocked HTTP.

    Args:
        monkeypatch: Pytest fixture.
        routes: Mapping of (method, path) to JSON body.

    Returns:
        Tuple of service and captured calls.
    """
    calls = []
    transport = SyncTransport(
        base_url="https://graph.facebook.com/v26.0",
        access_token="secret",
        timeout=TimeoutConfig(),
        retry=RetryConfig(max_attempts=1, jitter=False),
    )

    def fake_request(self, method, url, **kwargs):
        calls.append((method, url, kwargs))
        path = url.replace("https://graph.facebook.com/v26.0", "")
        request = httpx.Request(method, url)
        return httpx.Response(
            200, json=routes.get((method, path), {"success": True}), request=request
        )

    monkeypatch.setattr(httpx.Client, "request", fake_request)
    return GroupService(transport, "123"), calls


def test_group_lifecycle(monkeypatch):
    """Group create/list/get/update/delete follow the Groups API."""
    routes = {
        ("POST", "/123/groups"): {"id": GROUP_ID, "invite_link": "https://chat.whatsapp.com/x"},
        ("GET", "/123/groups"): {"data": [{"id": GROUP_ID, "subject": "Team"}]},
        ("GET", f"/{GROUP_ID}"): {"id": GROUP_ID, "subject": "Team"},
        ("POST", f"/{GROUP_ID}"): {"id": GROUP_ID, "subject": "Renamed"},
    }
    service, calls = _service(monkeypatch, routes)
    created = service.create_group(GroupCreate(subject="Team"))
    assert created.id == GROUP_ID and created.invite_link.startswith("https://")
    assert service.list_groups()[0].subject == "Team"
    assert service.get_group(GROUP_ID).id == GROUP_ID
    assert service.update_group(GROUP_ID, subject="Renamed").subject == "Renamed"
    assert service.delete_group(GROUP_ID) is True
    create_call = [c for c in calls if c[0] == "POST" and c[1].endswith("/groups")][0]
    assert create_call[2]["json"]["join_approval_mode"] == "auto_approve"


def test_join_requests_and_removal(monkeypatch):
    """Join-request moderation and participant removal hit scoped paths."""
    routes = {
        ("GET", f"/{GROUP_ID}/join_requests"): {"data": [{"id": "r-1", "wa_id": "919"}]},
    }
    service, calls = _service(monkeypatch, routes)
    assert service.list_join_requests(GROUP_ID)[0].wa_id == "919"
    assert service.approve_join_request(GROUP_ID, "r-1") is True
    assert service.reject_join_request(GROUP_ID, "r-2") is True
    assert service.remove_participants(GROUP_ID, ["919"]) is True
    paths = [c[1] for c in calls]
    assert f"https://graph.facebook.com/v26.0/{GROUP_ID}/participants" in paths


def test_group_envelope_and_pin_serialization():
    """Group envelopes set recipient_type; pins serialize per Meta docs."""
    envelope = OutboundMessage(
        to=GROUP_ID, content=TextMessage(body="Hi team"), recipient_type="group"
    )
    payload = serialize_envelope(envelope)
    assert payload["recipient_type"] == "group"
    assert payload["to"] == GROUP_ID
    pin = serialize_envelope(
        OutboundMessage(
            to=GROUP_ID,
            content=PinMessage(operation="pin", message_id="w-1", expiration_days=4),
            recipient_type="group",
        )
    )
    assert pin["type"] == "pin"
    assert pin["pin"] == {"type": "pin", "message_id": "w-1", "expiration_days": 4}


def test_call_webhook_fixture_parses():
    """Call connect webhooks normalize with direction and SDP type."""
    events = parse_body(
        open("tests/fixtures/webhooks/call_connect.json", "rb").read(), api_version="v26.0"
    )
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, WebhookCallEvent)
    assert event.call_id == "wacid.call-1"
    assert event.direction == "USER_INITIATED"
    assert event.sdp_type == "offer"
    assert event.raw["session"]["sdp"].startswith("v=0")


def test_group_message_carries_group_id_and_bsuid():
    """Group inbound messages expose group and BSUID identities."""
    from pathlib import Path

    raw = (Path("tests/fixtures/webhooks/message_received.json")).read_bytes()
    events = parse_body(raw)
    assert events[0].group_id == ""
    grouped = {
        "entry": [
            {
                "changes": [
                    {
                        "value": {
                            "metadata": {"phone_number_id": "123"},
                            "contacts": [
                                {"wa_id": "919", "user_id": "bsuid-1", "parent_user_id": "p-1"}
                            ],
                            "messages": [
                                {
                                    "from": "919",
                                    "id": "w-g1",
                                    "timestamp": "1",
                                    "type": "text",
                                    "group_id": GROUP_ID,
                                    "text": {"body": "Hi"},
                                }
                            ],
                        }
                    }
                ]
            }
        ]
    }
    import json

    events = parse_body(json.dumps(grouped).encode())
    assert events[0].group_id == GROUP_ID
    assert events[0].user_id == "bsuid-1"
    assert events[0].parent_user_id == "p-1"
