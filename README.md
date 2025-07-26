<div align="center">
  <h1>whatsloon</h1>
  <p>A Python wrapper facilitating seamless integration with the <a href="https://developers.facebook.com/docs/whatsapp/cloud-api">WhatsApp Cloud API</a>. Streamline your messaging workflows and enhance user engagement with this efficient toolkit.
  </p>
  <a href="https://pepy.tech/projects/whatsloon"><img src="https://static.pepy.tech/badge/whatsloon" alt="PyPI Downloads"></a>
  <a href="https://pepy.tech/projects/whatsloon"><img src="https://static.pepy.tech/badge/whatsloon/month" alt="PyPI Downloads"></a>
  <a href="https://pepy.tech/projects/whatsloon"><img src="https://static.pepy.tech/badge/whatsloon/week" alt="PyPI Downloads"></a>
</div>


## Overview
whatsloon is a robust Python SDK for the WhatsApp Cloud API. It provides a comprehensive set of mixin classes and utilities to send all supported WhatsApp message types, including text, media, interactive, template, location, reaction, sticker, and more. The package is designed for both synchronous and asynchronous workflows, with strong validation and error handling.


## Features
- Send Text, Image, Video, Audio, and Document messages
- Send Interactive messages: Lists, Reply Buttons, Flows, CTA buttons
- Send Location and Location Request messages
- Send Contact and Address messages
- Send Template messages (with components)
- Send Stickers and Reactions
- Send Typing Indicators
- Mark messages as Read
- Robust validation for API limits (e.g., button/section/row limits)
- Both synchronous and asynchronous support (requests and httpx)
- Clear error handling and logging


## Key Components
- Mixin Classes: Each message type (text, image, video, audio, document, list, flow, reply buttons, template, sticker, reaction, location, location request, contact, address, typing indicator, read receipt) is implemented as a robust, reusable mixin class.
- WhatsAppBaseClient: Easily compose your own client by combining mixins for only the features you need.
- Validation: All payload builders validate API limits and required fields.
- Async & Sync: All senders support both synchronous (requests) and asynchronous (httpx) usage.


## Installation
```sh
pip install whatsloon
```



## Usage Examples


### 1. Using WhatsAppCloudAPIClient (All Features, Easiest)
```python
from whatsloon import WhatsAppCloudAPIClient

client = WhatsAppCloudAPIClient(
    access_token="YOUR_API_KEY",
    phone_number_id="phone_number_id",
    recipient_country_code="91",
    recipient_mobile_number="9876543210",
)

# Synchronous usage
result = client.send_text_message("Hello, world!", preview_url=True)
print(result)

# Asynchronous usage
import asyncio
async def main():
    result = await client.async_send_text_message("Hello async!", preview_url=True)
    print(result)
asyncio.run(main())

# Send an image (sync)
result = client.send_image_message(media_id="MEDIA_ID", caption="A photo")
print(result)

# Send an image (async)
async def main_img():
    result = await client.async_send_image_message(media_id="MEDIA_ID", caption="Async photo")
    print(result)
asyncio.run(main_img())
```

### 2. Composing Your Own Client (Selected Features Only)
```python
# Import mixins directly from the package root
from whatsloon import WhatsAppBaseClient, TextSender, ImageSender

class MyWhatsAppClient(WhatsAppBaseClient, TextSender, ImageSender):
    pass

client = MyWhatsAppClient(
    access_token="YOUR_API_KEY",
    phone_number_id="phone_number_id",
    recipient_country_code="91",
    recipient_mobile_number="9876543210",
)

# Use only the features you mix in
result = client.send_text_message("Hello, world!", preview_url=True)
print(result)
```


### 3. Without Mixins (Direct Usage)
```python
from whatsloon import WhatsAppBaseClient

class SimpleClient(WhatsAppBaseClient):
    pass

client = SimpleClient(
    access_token="YOUR_API_KEY",
    phone_number_id="phone_number_id",
    recipient_country_code="91",
    recipient_mobile_number="9876543210",
)

# You can use the generic send_message method for custom payloads:
payload = {
    "type": "text",
    "text": {"body": "Hello from custom payload!"}
}
result = client.send_message(payload)
print(result)

# Async version
import asyncio
async def main():
    result = await client.async_send_message(payload)
    print(result)
asyncio.run(main())
```


## Testing
whatsloon includes comprehensive tests for all mixins, message types, and integration scenarios.

- **Test Dependencies:**
  - Requires `pytest` (and optionally `pytest-asyncio` for async tests)
  - Install with: `pip install -r requirements.txt` (if provided) or `pip install pytest pytest-asyncio`

- **Running All Tests:**
  ```sh
  pytest tests/
  ```

- **Running a Specific Test File:**
  ```sh
  pytest tests/test_text.py
  ```

- **Test Coverage:**
  To check coverage (if `pytest-cov` is installed):
  ```sh
  pytest --cov=whatsloon tests/
  ```

- **Contributing Tests:**
  - Add new tests in the `tests/` directory, following the pattern `test_<module>.py`.
  - Each test function should include a docstring explaining its purpose and expected input/output.
  - Edge cases and error handling are strongly encouraged.


## Contributing

Contributions are welcome! To contribute to whatsloon:

- **Bug Reports & Feature Requests:**
  - Please use the [GitHub Issues](https://github.com/maharanasarkar/whatsloon/issues) page to report bugs or suggest features.

- **Pull Requests:**
  - Fork the repository and create a new branch for your feature or fix.
  - Ensure your code follows the existing style and includes type hints and docstrings.
  - Add or update tests as appropriate.
  - Run all tests locally with `pytest` before submitting.
  - Submit a pull request with a clear description of your changes.

- **Code Style:**
  - We recommend using `black` for formatting and `flake8` for linting.
  - All public APIs should have type hints and Google-style docstrings.

Thank you for helping improve whatsloon!