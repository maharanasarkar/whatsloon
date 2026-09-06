<div align="center">
  <h1>whatsloon</h1>
  <p>Python SDK for the <a href="https://developers.facebook.com/docs/whatsapp/cloud-api">WhatsApp Cloud API</a> — sync + async, typed, tested.</p>
  <a href="https://pypi.org/project/whatsloon/"><img src="https://img.shields.io/pypi/v/whatsloon" alt="PyPI version"></a>
  <a href="https://github.com/maharanasarkar/whatsloon/actions/workflows/ci.yml"><img src="https://github.com/maharanasarkar/whatsloon/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <a href="https://codecov.io/gh/maharanasarkar/whatsloon"><img src="https://codecov.io/gh/maharanasarkar/whatsloon/branch/main/graph/badge.svg" alt="Coverage"></a>
  <a href="https://maharanasarkar.github.io/whatsloon/"><img src="https://img.shields.io/badge/docs-mkdocs-blue" alt="Docs"></a>
  <a href="https://pypistats.org/packages/whatsloon"><img src="https://img.shields.io/pypi/dm/whatsloon" alt="Downloads"></a>
  <a href="https://github.com/maharanasarkar/whatsloon/blob/main/LICENSE"><img src="https://img.shields.io/pypi/l/whatsloon" alt="License: MIT"></a>
  <img src="https://img.shields.io/pypi/pyversions/whatsloon" alt="Python versions">
</div>

## Overview

`whatsloon` wraps the WhatsApp Cloud API (`graph.facebook.com`) with composable mixins for every message type: text, image, video, audio, document, sticker, reaction, location, contacts, templates, interactive lists / reply buttons / CTA / flows, typing indicators, and read receipts.

- Sync via `requests`, async via `httpx`
- Validated payload builders with WhatsApp API limits
- `{"success": bool, "data" | "error"}` result shape + `logging`
- Full test suite, typed package (`py.typed`), docs on GitHub Pages

## Installation

```sh
pip install whatsloon
```

Requires Python >=3.9.

## Quickstart

```python
from whatsloon import WhatsAppCloudAPIClient

client = WhatsAppCloudAPIClient(
    access_token="YOUR_API_KEY",
    phone_number_id="phone_number_id",
    recipient_country_code="91",
    recipient_mobile_number="9876543210",
)

result = client.send_text_message("Hello, world!", preview_url=True)
print(result)
```

Async:

```python
import asyncio
from whatsloon import WhatsAppCloudAPIClient

async def main():
    client = WhatsAppCloudAPIClient(
        access_token="YOUR_API_KEY",
        phone_number_id="phone_number_id",
        recipient_country_code="91",
        recipient_mobile_number="9876543210",
    )
    print(await client.async_send_text_message("Hello async!"))

asyncio.run(main())
```

Custom client with only needed features:

```python
from whatsloon import WhatsAppBaseClient, TextSender, ImageSender

class MyClient(WhatsAppBaseClient, TextSender, ImageSender):
    pass
```

See [`docs/quickstart.md`](docs/quickstart.md), [`docs/usage.md`](docs/usage.md), and [`examples/`](examples/) for more.

Full docs: https://maharanasarkar.github.io/whatsloon/

## Features

- Text, image, video, audio, document, sticker
- Interactive: lists, reply buttons, CTA, flows
- Location + location request, contacts, address
- Templates with components, reactions, typing indicators, read receipts
- Sync + async for every sender

## Development

```sh
git clone https://github.com/maharanasarkar/whatsloon.git
cd whatsloon
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pre-commit install
pytest
ruff check .
ruff format --check .
mypy whatsloon
python -m build
```

See [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), [SECURITY.md](SECURITY.md).

## Testing

```sh
pip install -e ".[test]"
pytest
pytest --cov=whatsloon tests/
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md). Releases are cut from tags `v*` via Trusted Publishing to PyPI.

## License

MIT — see [LICENSE](LICENSE).
