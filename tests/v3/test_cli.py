"""CLI tests with stubbed clients and fixtures."""

from pathlib import Path

import pytest

import os

from whatsloon.cli import commands

import importlib

cli_main = importlib.import_module("whatsloon.cli.main")
from whatsloon.webhooks.verifier import compute_signature

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "webhooks"


def test_init_scaffolds_env(tmp_path, capsys):
    """Init writes env templates without clobbering existing files."""
    assert cli_main.main(["init", "--dir", str(tmp_path)]) == 0
    env_file = tmp_path / ".env"
    assert "WHATSAPP_ACCESS_TOKEN" in env_file.read_text()
    assert cli_main.main(["init", "--dir", str(tmp_path)]) == 0
    assert "keeping existing" in capsys.readouterr().out


def test_migrate_reports_legacy_usage(tmp_path, capsys):
    """Migrate audits report legacy calls with v3 mappings."""
    (tmp_path / "bot.py").write_text(
        "from whatsloon import WhatsAppCloudAPIClient\nc.send_text_message('hi')\n"
    )
    (tmp_path / "clean.py").write_text("print('v3 only')\n")
    assert commands.cmd_migrate(tmp_path) == 0
    out = capsys.readouterr().out
    assert "WhatsAppCloudAPIClient" in out and "wa.messages.send_text" in out
    assert "clean.py" not in out


def test_webhook_verify_and_replay(capsys):
    """Deliveries verify by signature and replay through the pipeline."""
    body = (FIXTURES / "message_received.json").read_bytes()
    signature = compute_signature("s3cret", body)
    assert commands.cmd_webhook_verify(FIXTURES / "message_received.json", "s3cret", signature) == 0
    assert "verify: OK" in capsys.readouterr().out
    assert (
        commands.cmd_webhook_verify(
            FIXTURES / "message_received.json", "s3cret", signature, replay=True
        )
        == 0
    )
    assert "handled" in capsys.readouterr().out
    assert (
        commands.cmd_webhook_verify(FIXTURES / "message_received.json", "s3cret", "sha256=x") == 1
    )


def test_send_and_doctor_with_stubbed_client(monkeypatch, capsys):
    """Send and doctor run against stubbed clients."""
    from whatsloon.client import SendMessageResult

    class StubMessages:
        def send_text(self, **kwargs):
            return SendMessageResult(message_id="wamid.cli-1", to=kwargs["to"])

    class StubBusiness:
        def get_phone_number(self, phone_id):
            from whatsloon.business.models import PhoneNumber

            return PhoneNumber(id=phone_id, display_phone_number="+919000000000")

    class StubClient:
        def __init__(self, *args, **kwargs):
            self.messages = StubMessages()
            self.business = StubBusiness()
            self.phone_number_id = "123"
            self.version = type("V", (), {"value": "v26.0"})()

        def close(self):
            pass

    monkeypatch.setenv("WHATSAPP_ACCESS_TOKEN", "t")
    monkeypatch.setenv("WHATSAPP_PHONE_NUMBER_ID", "123")
    monkeypatch.setattr(commands, "build_client", lambda **kw: StubClient())
    assert commands.cmd_send("919876543210", "Hi", None, "en_US") == 0
    assert "wamid.cli-1" in capsys.readouterr().out
    assert commands.cmd_doctor() == 0
    out = capsys.readouterr().out
    assert out.strip().splitlines()[-1] == "connectivity: OK"
    assert "+919000000000" not in out
    assert "919000000000" not in out


def test_flow_keygen_writes_private_key(tmp_path):
    """Keygen writes a private key and prints the public half."""
    pytest.importorskip("cryptography")
    private = tmp_path / "flow.pem"
    assert commands.cmd_flow_keygen(private) == 0
    assert "BEGIN PRIVATE KEY" in private.read_text()
    if os.name == "posix":
        assert (private.stat().st_mode & 0o777) == 0o600


def test_parser_commands_registered():
    """All documented subcommands exist."""
    parser = cli_main.build_parser()
    for command in ("init", "doctor", "send", "webhook", "template", "flow", "migrate"):
        assert command in parser._subparsers._group_actions[0].choices
