# Typed messages

The v3 client exposes every 2.x sender through `wa.messages` with typed
Pydantic models. Serialization is version-aware and byte-identical to the
2.x builders (proven by parity tests).

## Quickstart

```python
from whatsloon import WhatsApp
from whatsloon.messages.models import OutboundMessage, TextMessage

wa = WhatsApp(access_token="...", phone_number_id="...")
result = wa.messages.send(OutboundMessage(to="919876543210", content=TextMessage(body="Hello!")))
print(result.message_id)
```

Per-type helpers cover every sender:

```python
wa.messages.send_image(to="919876543210", media_id="...")
wa.messages.send_template(to="919876543210", template_name="hello", language_code="en_US")
wa.messages.mark_read(message_id="wamid....")
```

Replies attach to any content:

```python
wa.messages.send_text(to="919876543210", body="Got it!", reply_to="wamid....")
```

Async mirrors sync through shared builders:

```python
async with WhatsApp.async_client(access_token="...", phone_number_id="...") as wa:
    await wa.messages.send_text(to="919876543210", body="Hello async!")
```

## 2.x mapping

| 2.x call | v3 equivalent |
| --- | --- |
| `send_text_message` | `messages.send_text` / `TextMessage` |
| `send_image/video/audio/document/sticker_message` | `messages.send_image/...` |
| `send_reaction_message` | `messages.send_reaction` |
| `send_location_message` | `messages.send_location` |
| `send_contact_message` | `messages.send_contacts` |
| `send_template_message` | `messages.send_template` |
| `send_list_message` | `messages.send_list` + `ListBuilder` |
| `send_reply_buttons_message` | `messages.send_reply_buttons` + `ButtonsBuilder` |
| `send_cta_message` | `messages.send_cta` |
| `send_flow_message` | `messages.send_flow` |
| `send_address_message` | `messages.send_address` |
| `send_location_request_message` | `messages.send_location_request` |
| `send_typing_indicator` | `messages.send_typing` |
| `mark_message_as_read` | `messages.mark_read` |
| `send_contextual_reply` | any send with `reply_to=` |

The 2.x classes remain available under `whatsloon.compat` with a
deprecation warning.
