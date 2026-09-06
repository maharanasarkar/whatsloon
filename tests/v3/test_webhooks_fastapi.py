"""FastAPI webhook adapter tests."""

from pathlib import Path

import pytest

fastapi = pytest.importorskip("fastapi")

from fastapi import FastAPI
from fastapi.testclient import TestClient

from whatsloon.persistence.repositories import InMemoryEventRepository
from whatsloon.webhooks.fastapi import create_webhook_router
from whatsloon.webhooks.processor import WebhookProcessor
from whatsloon.webhooks.router import EventRouter
from whatsloon.webhooks.verifier import compute_signature

FIXTURES = Path(__file__).resolve().parent.parent / "fixtures" / "webhooks"
SECRET = "adapter-secret"


def _app():
    """Build a test app with a recording handler.

    Returns:
        Tuple of test client and handled list.
    """
    router = EventRouter()
    handled = []
    router.register("message.received", handled.append)
    processor = WebhookProcessor(
        router=router,
        events=InMemoryEventRepository(),
        tenant_resolver=lambda event: "t-1",
    )
    app = FastAPI()
    app.include_router(
        create_webhook_router(processor, app_secret=SECRET, verify_token="verify-me")
    )
    return TestClient(app), handled


def test_handshake_and_delivery():
    """Handshake echoes challenges; signed deliveries ack with outcomes."""
    client, handled = _app()
    response = client.get(
        "/webhooks/whatsapp",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "verify-me",
            "hub.challenge": "ch-7",
        },
    )
    assert response.status_code == 200
    assert response.text == "ch-7"
    assert (
        client.get(
            "/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong",
                "hub.challenge": "ch-7",
            },
        ).status_code
        == 403
    )
    body = (FIXTURES / "message_received.json").read_bytes()
    delivery = client.post(
        "/webhooks/whatsapp",
        content=body,
        headers={"X-Hub-Signature-256": compute_signature(SECRET, body)},
    )
    assert delivery.status_code == 200
    assert delivery.json()["results"][0]["outcome"] == "handled"
    assert len(handled) == 1
    tampered = client.post(
        "/webhooks/whatsapp",
        content=b"tampered",
        headers={"X-Hub-Signature-256": "sha256=wrong"},
    )
    assert tampered.status_code == 401
