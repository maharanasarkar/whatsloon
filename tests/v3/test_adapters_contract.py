"""Adapter contract tests loading version fixtures."""

import json
from pathlib import Path

from whatsloon.api_versions.registry import get_adapter

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "api_versions"


def _load(version, name):
    """Load a fixture payload.

    Args:
        version: Adapter version directory.
        name: Fixture file name.

    Returns:
        Decoded JSON payload.
    """
    return json.loads((FIXTURES / version / name).read_text(encoding="utf-8"))


def test_cross_version_text_serialization():
    """Same domain operation serializes per version with stable core fields."""
    payloads = [
        get_adapter(version).build_text_payload(to="919876543210", body="Hi")
        for version in ("v19.0", "v20.0", "v26.0")
    ]
    for payload in payloads:
        assert payload["messaging_product"] == "whatsapp"
        assert payload["to"] == "919876543210"
        assert payload["text"]["body"] == "Hi"


def test_success_fixtures_normalize_message_id():
    """Success fixtures yield message IDs and preserve unknown fields."""
    for version, dirname, fixture, expected in (
        ("v19.0", "v19", "text_send_success.json", "wamid.v19-text-1"),
        ("v20.0", "v20", "text_send_success.json", "wamid.v20-text-1"),
        ("v26.0", "v26", "text_send_success.json", "wamid.v26-text-1"),
    ):
        adapter = get_adapter(version)
        normalized = adapter.normalize_send_result(_load(dirname, fixture))
        assert normalized["message_id"] == expected
        assert normalized["raw"]["contacts"][0]["wa_id"] == "919876543210"


def test_failure_fixture_translates_to_auth_error():
    """Failure fixtures translate through the adapter boundary."""
    from whatsloon.exceptions import AuthenticationError

    adapter = get_adapter("v26.0")
    payload = _load("v26", "auth_error.json")
    err = adapter.translate_error(status_code=401, payload=payload, headers={})
    assert isinstance(err, AuthenticationError)
    assert err.code == 190


def test_unknown_fields_do_not_break_parsing():
    """Extra Meta fields survive normalization instead of failing."""
    adapter = get_adapter("v19.0")
    payload = {"messages": [{"id": "w-9", "new_field": True}], "future": {"x": 1}}
    normalized = adapter.normalize_send_result(payload)
    assert normalized["message_id"] == "w-9"
    assert normalized["raw"]["future"] == {"x": 1}
