# Examples

Copy `examples/.env.example` to `.env` and fill in your credentials, or export the variables:

```bash
cp examples/.env.example .env
export ACCESS_TOKEN=... PHONE_NUMBER_ID=... RECIPIENT_MOBILE_NUMBER=...
```

Run an example:

```bash
python examples/basic_text.py
python examples/template_message.py
python examples/custom_client.py
python examples/image_async.py
```

- `basic_text.py`: send a sync text message.
- `image_async.py`: send an image asynchronously.
- `template_message.py`: send an approved template.
- `custom_client.py`: compose a minimal client from mixins.
