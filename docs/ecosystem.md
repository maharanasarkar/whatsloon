# Ecosystem: testing, CLI, migration

## Testing (`whatsloon.testing`)

```python
from whatsloon.testing import MockMetaServer, make_fake_client

client, fake = make_fake_client([{"messages": [{"id": "wamid.x"}]}])
result = client.messages.send_text(to="...", body="Hi")
assert fake.seen[0].json_body["text"]["body"] == "Hi"
```

`MockMetaServer` serves httpx-level routes for integration-style tests,
including Meta-shaped errors for failure paths.

## CLI (`whatsloon` command)

```sh
whatsloon init --dir ./bot
whatsloon doctor
whatsloon send --to 919876543210 --body "Hello!"
whatsloon send --to 919876543210 --template hello --language en_US
whatsloon webhook --file delivery.json --app-secret ... --signature ... [--replay]
whatsloon template list --waba WABA_ID
whatsloon flow keygen --private-key flow.pem
whatsloon migrate --dir ./src
```

`migrate` audits 2.x usage and prints the v3 mapping; it never modifies
files. Credentials come from the environment or `--env-file` (never echoed).

## Migration from 2.x

1. Run `whatsloon migrate --dir` for the call inventory.
2. Replace the pinned-recipient client with `WhatsApp(...)` + per-send `to=`.
3. Swap each `send_*` call per `docs/messages.md`.
4. Keep `whatsloon.compat` imports working during the transition; they warn.
