"""Flow Data Exchange endpoint with Meta encryption."""

import os

from fastapi import FastAPI, Request, Response

from whatsloon.flows.crypto import FlowSession, decrypt_request

PRIVATE_KEY = os.environ.get("FLOW_PRIVATE_KEY", "")
APP_SECRET = os.environ.get("WHATSAPP_APP_SECRET", "")


def build_app() -> FastAPI:
    """Build the Flow endpoint application.

    Returns:
        Configured application.
    """
    app = FastAPI(title="whatsloon flow endpoint")

    @app.post("/flow")
    async def flow_endpoint(request: Request) -> Response:
        """Decrypt, route, and re-encrypt one Flow exchange.

        Args:
            request: Incoming Meta request.

        Returns:
            Encrypted response as plain text.
        """
        from whatsloon.webhooks.verifier import verify_signature

        raw = await request.body()
        payload = await request.json()
        verify_signature(APP_SECRET or None, raw, request.headers.get("X-Hub-Signature-256"))
        body, aes_key, iv = decrypt_request(
            payload["encrypted_flow_data"],
            payload["encrypted_aes_key"],
            payload["initial_vector"],
            PRIVATE_KEY,
        )
        session = FlowSession(body=body, aes_key=aes_key, iv=iv)
        action = body.get("action")
        if action == "ping":
            response = {"version": body.get("version", "3.0"), "data": {"status": "active"}}
        else:
            response = {
                "version": body.get("version", "3.0"),
                "screen": body.get("screen", "SUCCESS"),
                "data": {},
            }
        return Response(content=session.encrypt(response), media_type="text/plain")

    return app


app = build_app()
