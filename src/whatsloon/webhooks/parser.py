"""Version-aware webhook envelope parsing.

Parsing walks the Meta ``entry/changes/value`` structure and normalizes each
message and status into typed events. Anything unrecognized becomes an
:class:`UnknownEvent` with the raw envelope preserved — parsing never drops
data and never raises for unknown shapes (only for malformed JSON).
"""

from __future__ import annotations

import json
from typing import Any, Optional

from whatsloon.webhooks.events import (
    NormalizedEvent,
    UnknownEvent,
    WebhookMessageReceived,
    WebhookMessageStatus,
)


def parse_body(raw_body: bytes, *, api_version: str = "") -> list[NormalizedEvent]:
    """Parse raw webhook bytes into normalized events.

    Args:
        raw_body: Raw request bytes exactly as received.
        api_version: Adapter version used for normalization.

    Returns:
        Normalized events, one per message/status plus unknowns.

    Raises:
        InvalidPayloadError: If the body is not valid JSON or not an object.
    """
    from whatsloon.exceptions import InvalidPayloadError

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as exc:
        raise InvalidPayloadError("Webhook body is not valid JSON.") from exc
    if not isinstance(payload, dict):
        raise InvalidPayloadError("Webhook body must be a JSON object.")
    return parse_envelope(payload, api_version=api_version)


def parse_envelope(payload: dict[str, Any], *, api_version: str = "") -> list[NormalizedEvent]:
    """Normalize a decoded webhook envelope.

    Args:
        payload: Decoded webhook JSON.
        api_version: Adapter version used for normalization.

    Returns:
        Normalized events; unknown content becomes :class:`UnknownEvent`.
    """
    entries = payload.get("entry")
    if not isinstance(entries, list) or not entries:
        return [UnknownEvent(api_version=api_version, reason="missing entry", raw=payload)]
    events: list[NormalizedEvent] = []
    for entry in entries:
        if not isinstance(entry, dict):
            events.append(
                UnknownEvent(
                    api_version=api_version, reason="malformed entry", raw={"entry": entry}
                )
            )
            continue
        for change in entry.get("changes", []) or []:
            events.extend(_parse_change(change, api_version=api_version))
    return events or [UnknownEvent(api_version=api_version, reason="empty envelope", raw=payload)]


def _parse_change(change: Any, *, api_version: str) -> list[NormalizedEvent]:
    """Normalize one entry change.

    Args:
        change: Change object.
        api_version: Adapter version stamp.

    Returns:
        Normalized events for the change.
    """
    if not isinstance(change, dict):
        return [
            UnknownEvent(api_version=api_version, reason="malformed change", raw={"change": change})
        ]
    value = change.get("value")
    if not isinstance(value, dict):
        return [UnknownEvent(api_version=api_version, reason="missing value", raw=change)]
    events: list[NormalizedEvent] = []
    phone_id = str(value.get("metadata", {}).get("phone_number_id", ""))
    identities = _contact_identities(value.get("contacts", []))
    for message in value.get("messages", []) or []:
        events.append(
            _parse_message(
                message, phone_id=phone_id, identities=identities, api_version=api_version
            )
        )
    for status in value.get("statuses", []) or []:
        events.append(_parse_status(status, api_version=api_version))
    for call in value.get("calls", []) or []:
        events.append(_parse_call(call, api_version=api_version))
    if not events:
        events.append(UnknownEvent(api_version=api_version, reason="unrecognized value", raw=value))
    return events


def _contact_identities(contacts: Any) -> dict[str, dict[str, str]]:
    """Map sender identifiers to BSUID identity pairs.

    Args:
        contacts: Raw contacts array.

    Returns:
        Mapping of wa_id to user/parent identifiers.
    """
    identities: dict[str, dict[str, str]] = {}
    if isinstance(contacts, list):
        for contact in contacts:
            if isinstance(contact, dict) and contact.get("wa_id"):
                identities[str(contact["wa_id"])] = {
                    "user_id": str(contact.get("user_id", "")),
                    "parent_user_id": str(contact.get("parent_user_id", "")),
                }
    return identities


def _parse_message(
    message: Any, *, phone_id: str, identities: dict[str, dict[str, str]], api_version: str
) -> NormalizedEvent:
    """Normalize one inbound message.

    Args:
        message: Raw message object.
        phone_id: Recipient phone number ID.
        identities: BSUID identity map keyed by sender.
        api_version: Adapter version stamp.

    Returns:
        Typed received event, or UnknownEvent for malformed entries.
    """
    if not isinstance(message, dict) or "id" not in message:
        return UnknownEvent(
            api_version=api_version, reason="malformed message", raw={"message": message}
        )
    kind = str(message.get("type", ""))
    text_body: Optional[str] = None
    text = message.get("text")
    if isinstance(text, dict) and isinstance(text.get("body"), str):
        text_body = text["body"]
    sender = str(message.get("from", ""))
    identity = identities.get(sender, {})
    return WebhookMessageReceived(
        api_version=api_version,
        message_id=str(message.get("id", "")),
        sender=sender,
        recipient_phone_id=phone_id,
        timestamp=str(message.get("timestamp", "")),
        message_type=kind,
        text_body=text_body,
        group_id=str(message.get("group_id", "")),
        user_id=identity.get("user_id", ""),
        parent_user_id=identity.get("parent_user_id", ""),
        raw=message,
    )


def _parse_call(call: Any, *, api_version: str) -> NormalizedEvent:
    """Normalize one voice call webhook object.

    Args:
        call: Raw call object.
        api_version: Adapter version stamp.

    Returns:
        Typed call event, or UnknownEvent for malformed entries.
    """
    from whatsloon.webhooks.events import WebhookCallEvent

    if not isinstance(call, dict) or "id" not in call:
        return UnknownEvent(api_version=api_version, reason="malformed call", raw={"call": call})
    session = call.get("session", {}) if isinstance(call.get("session"), dict) else {}
    return WebhookCallEvent(
        api_version=api_version,
        call_id=str(call.get("id", "")),
        call_event=str(call.get("event", "")),
        direction=str(call.get("direction", "")),
        caller=str(call.get("from", "")),
        callee=str(call.get("to", "")),
        timestamp=str(call.get("timestamp", "")),
        sdp_type=str(session.get("sdp_type", "")),
        raw=call,
    )
    kind = str(message.get("type", ""))
    text_body: Optional[str] = None
    text = message.get("text")
    if isinstance(text, dict) and isinstance(text.get("body"), str):
        text_body = text["body"]
    return WebhookMessageReceived(
        api_version=api_version,
        message_id=str(message.get("id", "")),
        sender=str(message.get("from", "")),
        recipient_phone_id=phone_id,
        timestamp=str(message.get("timestamp", "")),
        message_type=kind,
        text_body=text_body,
        raw=message,
    )


def _parse_status(status: Any, *, api_version: str) -> NormalizedEvent:
    """Normalize one delivery status.

    Args:
        status: Raw status object.
        api_version: Adapter version stamp.

    Returns:
        Typed status event, or UnknownEvent for malformed entries.
    """
    if not isinstance(status, dict) or "id" not in status:
        return UnknownEvent(
            api_version=api_version, reason="malformed status", raw={"status": status}
        )
    return WebhookMessageStatus(
        api_version=api_version,
        message_id=str(status.get("id", "")),
        status=str(status.get("status", "")),
        recipient=str(status.get("recipient_id", "")),
        timestamp=str(status.get("timestamp", "")),
        raw=status,
    )


__all__ = ["parse_body", "parse_envelope"]
