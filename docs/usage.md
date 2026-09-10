# Usage

> **Legacy API (frozen).** This page covers the 2.x mixin-composed clients,
> which are frozen: no new features, only critical fixes. New code should use
> the [v3 client](messages.md) (`WhatsApp` with per-send `to=`), which has
> typed models, retries, and observability.

## Full client

Use `WhatsAppCloudAPIClient` for access to every feature:

```python
from whatsloon import WhatsAppCloudAPIClient

client = WhatsAppCloudAPIClient(
    access_token="ACCESS_TOKEN",
    phone_number_id="PHONE_NUMBER_ID",
    recipient_country_code="91",
    recipient_mobile_number="9876543210",
)
client.send_image_message(media_link="https://example.com/img.jpg", caption="Hi")
```

## Custom client composition

Compose only the mixins you need to keep your client small:

```python
from whatsloon import WhatsAppBaseClient, TextSender, ImageSender, TemplateSender


class MyClient(WhatsAppBaseClient, TextSender, ImageSender, TemplateSender):
    pass


client = MyClient(
    access_token="ACCESS_TOKEN",
    phone_number_id="PHONE_NUMBER_ID",
    recipient_country_code="91",
    recipient_mobile_number="9876543210",
)
client.send_text_message("Only text, image, and template support")
```

All mixins are importable from the package root, for example `TextSender`, `ImageSender`, `TemplateSender`, `VideoSender`, `DocumentSender`, and `WhatsAppBaseClient`.
