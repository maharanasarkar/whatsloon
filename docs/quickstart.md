# Quickstart

Install the package:

```bash
pip install whatsloon
```

Send a text message (sync):

```python
from whatsloon import WhatsAppCloudAPIClient

client = WhatsAppCloudAPIClient(
    access_token="ACCESS_TOKEN",
    phone_number_id="PHONE_NUMBER_ID",
    recipient_country_code="91",
    recipient_mobile_number="9876543210",
)
result = client.send_text_message("Hello from whatsloon!")
print(result)
```

Send a text message (async):

```python
import asyncio
from whatsloon import WhatsAppCloudAPIClient


async def main():
    client = WhatsAppCloudAPIClient(
        access_token="ACCESS_TOKEN",
        phone_number_id="PHONE_NUMBER_ID",
        recipient_country_code="91",
        recipient_mobile_number="9876543210",
    )
    result = await client.async_send_text_message("Hello async!")
    print(result)


asyncio.run(main())
```
