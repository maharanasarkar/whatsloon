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

## Authentication

API clients send `Authorization: Bearer <token>`. Browsers navigating links
cannot set headers, so pages also accept a `token` query parameter as an
explicit fallback for this reference console. Tokens in URLs can leak into
history and server logs — prefer header auth, short-lived tokens, and HTTPS.

Raw payload reveal additionally requires an `owner`/`operator` role, and
payloads are secret-redacted regardless of role.
