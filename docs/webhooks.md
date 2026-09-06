# Inbound webhooks

The pipeline is `raw bytes -> HMAC verify -> parse -> fingerprint/dedupe ->
persist -> route/filter -> handle (sync|async|queued) -> persist result -> ack`.

## Verification

Signatures use HMAC-SHA256 over the exact raw body and constant-time
comparison. Missing secrets, headers, or mismatches fail closed:

```python
from whatsloon.webhooks import verify_signature, verify_handshake

verify_signature(app_secret, raw_body, signature_header)
challenge = verify_handshake(mode=..., verify_token_expected=..., verify_token_received=..., challenge=...)
```

## Handling

```python
from whatsloon.persistence.repositories import InMemoryEventRepository
from whatsloon.webhooks import EventRouter, WebhookProcessor

router = EventRouter()
router.register("message.received", on_message)
router.set_fallback(on_unknown)

processor = WebhookProcessor(router=router, events=InMemoryEventRepository())
results = processor.process(raw_body, signature_header, app_secret=...)
```

Duplicates collapse to one handler run via event fingerprints. Handler
failures persist as `FAILED` without losing sibling events. Pass a `queue`
hook to defer handling; use `aprocess` for coroutine handlers.

## FastAPI

```python
from whatsloon.webhooks.fastapi import create_webhook_router

app.include_router(create_webhook_router(processor, app_secret=..., verify_token=...))
```

Unknown Meta shapes are preserved as `unknown` events — never dropped.
Raw payload retention is opt-in (`retain_raw=True`).
