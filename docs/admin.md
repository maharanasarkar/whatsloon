# Admin console

The reference console (`whatsloon[admin]`) pairs the JSON API with
server-rendered HTML pages (Jinja2 + HTMX, no JS build step). The same
masked view data powers both surfaces.

## Running it

```python
from whatsloon.admin.app import RepositoryBundle, create_app
from whatsloon.admin.auth import StaticTokenAuth, AdminUser
from whatsloon.persistence.repositories import (
    InMemoryConversationRepository,
    InMemoryEventRepository,
    InMemoryMessageRepository,
)

store = RepositoryBundle(
    conversations=InMemoryConversationRepository(),
    messages=InMemoryMessageRepository(),
    events=InMemoryEventRepository(),
)
auth = StaticTokenAuth({"ops-token": AdminUser(username="ops", tenant_id="*")})
app = create_app(store, auth)
```

```sh
uvicorn mymodule:app --host 127.0.0.1 --port 8000
```

Open `http://127.0.0.1:8000/ui/dashboard?tenant_id=t-1&token=ops-token`.

## Pages

| Page | Purpose |
| --- | --- |
| `/ui/dashboard` | Totals, failures, recent conversations |
| `/ui/conversations` | Conversation list with limits |
| `/ui/messages` | Filterable message list (status, direction) |
| `/ui/messages/{id}` | Detail, status history, privileged raw reveal |
| `/ui/events` | Webhook events with failure highlighting |

Filters submit as plain forms and upgrade to HTMX row swaps when JS runs,
so pages work with and without JavaScript. Every page has labeled regions,
a skip link, keyboard-native controls, and explicit empty and error states.

## Threads, search, and pagination

- Conversation IDs link to a chronological thread view (`/ui/conversations/{id}`).
- The messages page searches content substrings (`q`) and date bounds
  (`since`/`until` as YYYY-MM-DD); invalid dates are ignored, never errors.
- List pages paginate with prev/next links preserving active filters.

## Failure center

Failed events show a **Retry** button (and `POST /events/{id}/retry` on the
JSON API) that re-dispatches the stored event from its retained raw payload
and bumps the retry count. Retries require:

- a processor wired into `create_app(store, auth, processor=...)`, and
- retained raw payloads (`retain_raw=True`); otherwise the outcome reports
  `unavailable`, and unknown IDs report `missing`.

Without a processor the controls are hidden and the endpoint answers 501.

## Authentication

API clients send `Authorization: Bearer <token>`. Browsers navigating links
cannot set headers, so pages also accept a `token` query parameter as an
explicit fallback for this reference console. Tokens in URLs can leak into
history and server logs — prefer header auth, short-lived tokens, and HTTPS.

Raw payload reveal additionally requires an `owner`/`operator` role, and
payloads are secret-redacted regardless of role.

## Browser login

`/ui/login` accepts an API token and sets an `HttpOnly`, `SameSite=Lax`
session cookie (12h, in-memory server store), so navigation works without
tokens in URLs. `/ui/logout` clears it. Production deployments should use
persistent sessions plus CSRF protection; the reference store is a starting
point, not a finished auth system.

## Auto-persistence

Pass repositories to make the admin reflect live traffic without manual
wiring:

```python
from whatsloon.messages.service import MessageService

service = MessageService(
    adapter,
    transport,
    phone_number_id,
    message_store=messages,
    conversation_store=conversations,
    tenant_id="t-1",
)
```

Outbound sends then persist message + conversation records (storage
failures log a warning; the send result stays authoritative). Likewise,
`WebhookProcessor(..., message_store=..., conversation_store=...)`
materializes inbound messages at receipt time.

## Resource managers

Pass a v3 client to unlock management pages (hidden otherwise):

```python
app = create_app(store, auth, processor=processor, wa=whatsapp_client)
```

- `/ui/templates` — list/create per WABA (names are lowercase + underscores)
- `/ui/media` — multipart upload returning the media ID
- `/ui/groups` — list groups with invite links

Meta API failures render as error pages, never tracebacks.
