"""Media, template, and business resource usage."""

import os

from whatsloon import WhatsApp
from whatsloon.templates.models import TemplateSpec

ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "YOUR_API_KEY")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "phone_number_id")
WABA_ID = os.environ.get("WHATSAPP_WABA_ID", "waba_id")


def main() -> None:
    """Exercise resource services over the v3 client."""
    wa = WhatsApp(access_token=ACCESS_TOKEN, phone_number_id=PHONE_NUMBER_ID)
    upload = wa.media.upload_file("photo.jpg", "image/jpeg")
    print(upload.media_id)
    print(wa.templates.list_templates(WABA_ID))
    print(
        wa.templates.create_template(
            WABA_ID, TemplateSpec(name="hello", language="en_US", category="UTILITY")
        )
    )
    print([n.display_phone_number for n in wa.business.list_phone_numbers(WABA_ID)])
    wa.close()


if __name__ == "__main__":
    main()
