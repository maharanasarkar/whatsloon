"""Inbound webhook receiver over the v3 pipeline."""

import os

from fastapi import FastAPI

from whatsloon.persistence.repositories import InMemoryEventRepository
from whatsloon.webhooks.fastapi import create_webhook_router
from whatsloon.webhooks.processor import WebhookProcessor
from whatsloon.webhooks.router import EventRouter

APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "change-me")
VERIFY_TOKEN = os.environ.get("WHATSAPP_VERIFY_TOKEN", "change-me")


def on_message(event) -> None:
    """Log inbound message identifiers.

    Args:
        event: Normalized received event.
    """
    print(f"received {event.message_id} from {event.sender}: {event.text_body!r}")


def build_app() -> FastAPI:
    """Build the webhook FastAPI application.

    Returns:
        Configured application.
    """
    router = EventRouter()
    router.register("message.received", on_message)
    processor = WebhookProcessor(router=router, events=InMemoryEventRepository())
    app = FastAPI(title="whatsloon webhooks")
    app.include_router(
        create_webhook_router(processor, app_secret=APP_SECRET, verify_token=VERIFY_TOKEN)
    )
    return app


app = build_app()
