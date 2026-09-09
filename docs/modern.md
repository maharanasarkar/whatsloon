# Groups, calls, and Direct Send

## Groups (`wa.groups`)

```python
group = wa.groups.create_group(GroupCreate(subject="Team", join_approval_mode="approval_required"))
print(group.invite_link)
wa.groups.approve_join_request(group.id, "request-id")
wa.groups.remove_participants(group.id, ["919876543210"])
```

Groups are invite-only: members join via the invite link (there is no
add-participant endpoint); the business approves or rejects requests.
Group messaging reuses `wa.messages` with `recipient_type="group"`:

> Eligibility: numbers without Groups access get `ValidationAPIError`
> `(#131215) "This phone number is not eligible to access Groups APIs"`.
> This is a number capability, not a payload problem — verify eligibility
> in the Meta dashboard before debugging the request.

```python
from whatsloon.messages.models import OutboundMessage, TextMessage

wa.messages.send(
    OutboundMessage(to=group.id, content=TextMessage(body="Hi team"), recipient_type="group")
)
```

Pin messages with `PinMessage(operation="pin", message_id="...", expiration_days=4)`.

## Calls (`wa.calls`)

```python
call = wa.calls.connect(to="16315553602", sdp_offer="v=0\r\n...")
wa.calls.pre_accept(call_id=call["calls"][0]["id"], sdp_answer="v=0\r\n...")
wa.calls.accept(call_id="...", sdp_answer="v=0\r\n...")
wa.calls.terminate(call_id="...")
permission = wa.calls.get_permission("16315553602")
```

Inbound calls arrive as `call.event` webhooks with SDP offers; register a
`call.event` handler on the webhook router.

## Direct Send

Attach tracking data echoed back in webhooks:

```python
wa.messages.send_text(
    to="...",
    body="...",
)
envelope = OutboundMessage(
    to="...", content=TextMessage(body="..."), biz_opaque_callback_data="campaign-42"
)
wa.messages.send(envelope)
```

## Inbound coverage

Message events carry `group_id` plus BSUID `user_id`/`parent_user_id`;
call webhooks normalize to `call.event` with direction and SDP type.
See `examples/v3_modern.py`.
