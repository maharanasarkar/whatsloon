"""whatsloon command-line interface (stdlib argparse only)."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from whatsloon.cli import commands


def build_parser() -> argparse.ArgumentParser:
    """Build the CLI argument parser.

    Returns:
        Configured parser.
    """
    parser = argparse.ArgumentParser(prog="whatsloon", description="WhatsApp Cloud API toolkit.")
    parser.add_argument("--env-file", default=".env", help="Dotenv file to load.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Scaffold a project directory.")
    init.add_argument("--dir", default=".")

    sub.add_parser("doctor", help="Check credentials and connectivity.")

    send = sub.add_parser("send", help="Send a message.")
    send.add_argument("--to", required=True)
    send.add_argument("--body", default=None)
    send.add_argument("--template", default=None)
    send.add_argument("--language", default="en_US")

    webhook = sub.add_parser("webhook", help="Verify or replay a delivery file.")
    webhook.add_argument("--file", required=True)
    webhook.add_argument("--app-secret", default=os.environ.get("WHATSAPP_APP_SECRET", ""))
    webhook.add_argument("--signature", default=None)
    webhook.add_argument("--replay", action="store_true")

    template = sub.add_parser("template", help="Manage templates.")
    template.add_argument("action", choices=["list", "create", "delete"])
    template.add_argument("--waba", required=True)
    template.add_argument("--name", default="")
    template.add_argument("--language", default="en_US")

    flow = sub.add_parser("flow", help="Flow endpoint helpers.")
    flow.add_argument("action", choices=["keygen"])
    flow.add_argument("--private-key", default="flow_private.pem")

    migrate = sub.add_parser("migrate", help="Audit 2.x usage (report only).")
    migrate.add_argument("--dir", default=".")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI.

    Args:
        argv: Argument list; defaults to sys.argv.

    Returns:
        Exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    commands.load_env_file(Path(args.env_file))
    if args.command == "init":
        return commands.cmd_init(Path(args.dir))
    if args.command == "doctor":
        return commands.cmd_doctor()
    if args.command == "send":
        return commands.cmd_send(args.to, args.body, args.template, args.language)
    if args.command == "webhook":
        return commands.cmd_webhook_verify(
            Path(args.file), args.app_secret, args.signature, replay=args.replay
        )
    if args.command == "template":
        return commands.cmd_template(args.action, args.waba, args.name, args.language)
    if args.command == "flow":
        return commands.cmd_flow_keygen(Path(args.private_key))
    if args.command == "migrate":
        return commands.cmd_migrate(Path(args.dir))
    parser.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
