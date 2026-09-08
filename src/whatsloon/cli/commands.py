"""whatsloon CLI command implementations (stdlib only)."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Optional

ENV_TEMPLATE = """\
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_WABA_ID=your-waba-id
WHATSAPP_TO=919876543210
WHATSAPP_APP_SECRET=your-app-secret
WHATSAPP_VERIFY_TOKEN=your-verify-token
"""

_SECRET_PATTERNS = (
    re.compile(r"Bearer\s+[A-Za-z0-9._\-~+/=]+"),
    re.compile(
        r"(access_token|app_secret|verify_token|pin)\s*[:=]\s*['\"]?[^'\"\s,}]+", re.IGNORECASE
    ),
)
"""Patterns redacted from CLI error output so secrets never reach logs."""


def format_error(exc: BaseException) -> str:
    """Render an exception for CLI output with secrets redacted.

    Args:
        exc: The failure.

    Returns:
        Type name plus redacted message.
    """
    message = str(exc)
    for pattern in _SECRET_PATTERNS:
        message = pattern.sub("***", message)
    return f"{type(exc).__name__}: {message}"


def load_env_file(path: Path) -> dict[str, str]:
    """Load KEY=VALUE pairs from a dotenv file without overriding env.

    Args:
        path: Dotenv file path.

    Returns:
        Mapping of loaded values.
    """
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key, val = key.strip(), val.strip().strip("'\"")
        if key and key not in os.environ:
            os.environ[key] = val
            values[key] = val
    return values


def build_client(**overrides: Any) -> Any:
    """Build a v3 client from environment with explicit overrides.

    Args:
        **overrides: Constructor overrides.

    Returns:
        Configured :class:`WhatsApp` client.

    Raises:
        ConfigurationError: If credentials are missing.
    """
    from whatsloon.client import WhatsApp
    from whatsloon.exceptions import ConfigurationError

    token = overrides.pop("access_token", os.environ.get("WHATSAPP_ACCESS_TOKEN", ""))
    phone_id = overrides.pop("phone_number_id", os.environ.get("WHATSAPP_PHONE_NUMBER_ID", ""))
    if not token or not phone_id:
        raise ConfigurationError("Set WHATSAPP_ACCESS_TOKEN and WHATSAPP_PHONE_NUMBER_ID.")
    return WhatsApp(access_token=token, phone_number_id=phone_id, **overrides)


def cmd_init(directory: Path) -> int:
    """Scaffold a project directory with env template.

    Args:
        directory: Target directory.

    Returns:
        Exit code.
    """
    directory.mkdir(parents=True, exist_ok=True)
    env_file = directory / ".env"
    if env_file.exists():
        print(f"keeping existing {env_file}")
    else:
        env_file.write_text(ENV_TEMPLATE, encoding="utf-8")
        print(f"wrote {env_file}")
    print("Next: fill in credentials, then run 'whatsloon doctor'.")
    return 0


def cmd_doctor() -> int:
    """Check credentials, version, and connectivity.

    Returns:
        Exit code.
    """
    from whatsloon.config.versions import LATEST_VERSION

    try:
        client = build_client()
    except Exception as exc:
        print(f"config: FAIL ({format_error(exc)})")
        return 1
    print(f"config: OK (api_version={client.version.value}, latest={LATEST_VERSION})")
    try:
        number = client.business.get_phone_number(client.phone_number_id)
        print(f"connectivity: OK (display={number.display_phone_number or 'unknown'})")
    except Exception as exc:
        print(f"connectivity: FAIL ({format_error(exc)})")
        return 1
    finally:
        client.close()
    return 0


def cmd_send(to: str, body: Optional[str], template: Optional[str], language: str) -> int:
    """Send a text or template message.

    Args:
        to: Destination identifier.
        body: Text body for text sends.
        template: Template name for template sends.
        language: Template locale.

    Returns:
        Exit code.
    """
    try:
        client = build_client()
    except Exception as exc:
        print(f"config: FAIL ({format_error(exc)})")
        return 1
    try:
        if template:
            result = client.messages.send_template(
                to=to, template_name=template, language_code=language
            )
        elif body:
            result = client.messages.send_text(to=to, body=body)
        else:
            print("Provide --body or --template.")
            return 2
        print(f"sent: {result.message_id}")
        return 0
    except Exception as exc:
        print(f"send: FAIL ({format_error(exc)})")
        return 1
    finally:
        client.close()


def cmd_webhook_verify(
    path: Path, app_secret: str, signature: Optional[str], replay: bool = False
) -> int:
    """Verify and optionally replay a webhook delivery file.

    Args:
        path: Delivery body file.
        app_secret: App secret for verification.
        signature: Signature header value.
        replay: Whether to route through the pipeline.

    Returns:
        Exit code.
    """
    from whatsloon.persistence.repositories import InMemoryEventRepository
    from whatsloon.webhooks import EventRouter, WebhookProcessor, verify_signature
    from whatsloon.webhooks.parser import parse_body

    raw = path.read_bytes()
    try:
        verify_signature(app_secret or None, raw, signature)
    except Exception as exc:
        print(f"verify: FAIL ({format_error(exc)})")
        return 1
    print("verify: OK")
    events = parse_body(raw)
    for event in events:
        print(f"event: {event.event_type}")
    if replay:
        router = EventRouter()
        seen: list[str] = []
        router.set_fallback(lambda event: seen.append(event.event_type))
        processor = WebhookProcessor(router=router, events=InMemoryEventRepository())
        results = processor.process(raw, signature, app_secret=app_secret)
        for result in results:
            print(f"outcome: {result.event_type} -> {result.outcome}")
    return 0


def cmd_template(action: str, waba_id: str, name: str = "", language: str = "en_US") -> int:
    """List, create, or delete templates.

    Args:
        action: One of list, create, delete.
        waba_id: WhatsApp Business Account ID.
        name: Template name for create/delete.
        language: Template locale for create.

    Returns:
        Exit code.
    """
    from whatsloon.templates.models import TemplateSpec

    try:
        client = build_client()
    except Exception as exc:
        print(f"config: FAIL ({format_error(exc)})")
        return 1
    try:
        if action == "list":
            for template in client.templates.list_templates(waba_id):
                print(f"{template.name} [{template.status}] {template.language}")
        elif action == "create":
            created = client.templates.create_template(
                waba_id, TemplateSpec(name=name, language=language)
            )
            print(f"created: {created.id or created.name}")
        elif action == "delete":
            print(f"deleted: {client.templates.delete_template(waba_id, name)}")
        else:
            print(f"Unknown template action: {action}.")
            return 2
        return 0
    except Exception as exc:
        print(f"template: FAIL ({format_error(exc)})")
        return 1
    finally:
        client.close()


def cmd_flow_keygen(private_path: Path) -> int:
    """Generate an RSA keypair for Flow endpoints.

    Args:
        private_path: Destination for the private PEM (mode 0600).

    Returns:
        Exit code.
    """
    from whatsloon.flows.crypto import generate_keypair

    private_pem, public_pem = generate_keypair()
    private_path.write_text(private_pem, encoding="utf-8")
    try:
        os.chmod(private_path, 0o600)
    except OSError:
        pass
    print(public_pem)
    print(f"private key: {private_path} (upload public key to Meta)")
    return 0


LEGACY_PATTERNS = [
    (r"WhatsAppCloudAPIClient", "whatsloon.client.WhatsApp (context client, no pinned recipient)"),
    (r"send_text_message", "wa.messages.send_text"),
    (r"send_image_message|send_video_message|send_audio_message", "wa.messages.send_image/..."),
    (r"send_document_message|send_sticker_message", "wa.messages.send_document/send_sticker"),
    (r"send_template_message", "wa.messages.send_template"),
    (
        r"send_list_message|send_reply_buttons_message",
        "wa.messages.send_list/send_reply_buttons + builders",
    ),
    (
        r"send_cta_message|send_flow_message|send_address_message",
        "wa.messages.send_cta/send_flow/send_address",
    ),
    (
        r"send_reaction_message|send_location_message|send_contact_message",
        "wa.messages.send_reaction/send_location/send_contacts",
    ),
    (r"mark_message_as_read|send_typing_indicator", "wa.messages.mark_read/send_typing"),
    (r"send_contextual_reply", "any send with reply_to="),
    (r"recipient_country_code|recipient_mobile_number", "per-send `to=` (no pinned recipient)"),
]
"""Legacy usage patterns mapped to v3 equivalents."""


def cmd_migrate(directory: Path) -> int:
    """Audit a codebase for 2.x usage and print the v3 mapping.

    Args:
        directory: Codebase root to scan.

    Returns:
        Exit code (always zero; report-only, never modifies files).
    """
    hits: dict[str, list[str]] = {}
    for path in sorted(directory.rglob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for pattern, _ in LEGACY_PATTERNS:
            if re.search(pattern, text):
                hits.setdefault(pattern, []).append(str(path))
    if not hits:
        print("No 2.x usage detected.")
        return 0
    print("Legacy usage found (report only, nothing modified):")
    for pattern, replacement in LEGACY_PATTERNS:
        files = hits.get(pattern, [])
        if files:
            print(f"\n{pattern} -> {replacement}")
            for name in files[:20]:
                print(f"  {name}")
    return 0


__all__ = [
    "build_client",
    "cmd_doctor",
    "cmd_flow_keygen",
    "cmd_init",
    "cmd_migrate",
    "cmd_send",
    "cmd_template",
    "cmd_webhook_verify",
    "load_env_file",
]
