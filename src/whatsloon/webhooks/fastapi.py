"""FastAPI adapter for the webhook pipeline (``whatsloon[admin]`` extra)."""

from __future__ import annotations

from typing import Any as _Any
from typing import Optional

try:
    from fastapi import APIRouter, Header, Query, Request, Response
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Webhook FastAPI adapter requires the 'admin' extra: pip install 'whatsloon[admin]'."
    ) from exc

from whatsloon.webhooks.processor import WebhookProcessor
from whatsloon.webhooks.verifier import verify_handshake


def create_webhook_router(
    processor: WebhookProcessor,
    *,
    app_secret: _Any,
    verify_token: str,
    path: str = "/webhooks/whatsapp",
) -> APIRouter:
    """Create an APIRouter serving handshake and delivery endpoints.

    Args:
        processor: Configured pipeline processor.
        app_secret: App secret for signature verification (never logged).
        verify_token: Expected subscription verify token.
        path: Route path prefix.

    Returns:
        Configured router; mount with ``app.include_router``.
    """
    router = APIRouter()

    @router.get(path)
    async def handshake(
        hub_mode: Optional[str] = Query(default=None, alias="hub.mode"),
        hub_verify_token: Optional[str] = Query(default=None, alias="hub.verify_token"),
        hub_challenge: Optional[str] = Query(default=None, alias="hub.challenge"),
    ) -> Response:
        """Answer Meta subscription handshakes.

        Args:
            hub_mode: Handshake mode.
            hub_verify_token: Presented verify token.
            hub_challenge: Challenge to echo.

        Returns:
            Challenge response or 403 on mismatch.
        """
        from whatsloon.exceptions import InvalidPayloadError

        try:
            challenge = verify_handshake(
                mode=hub_mode,
                verify_token_expected=verify_token,
                verify_token_received=hub_verify_token,
                challenge=hub_challenge,
            )
        except InvalidPayloadError:
            return Response(status_code=403, content="forbidden")
        return Response(content=challenge, media_type="text/plain")

    @router.post(path)
    async def delivery(
        request: Request,
        signature: Optional[str] = Header(default=None, alias="X-Hub-Signature-256"),
    ) -> _Any:
        """Accept one webhook delivery and run the pipeline.

        Args:
            request: Incoming request.
            signature: Signature header value.

        Returns:
            Ack summary; verification failures map to 401/400 statuses.
        """
        from whatsloon.exceptions import InvalidPayloadError, InvalidSignatureError

        raw_body = await request.body()
        try:
            results = await processor.aprocess(raw_body, signature, app_secret=app_secret)
        except InvalidSignatureError:
            return Response(status_code=401, content="unauthorized")
        except InvalidPayloadError:
            return Response(status_code=400, content="bad request")
        return {"ok": True, "results": [r.__dict__ for r in results]}

    return router


__all__ = ["create_webhook_router"]
