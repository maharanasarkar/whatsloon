"""Media, template, and business resource usage."""

import os

from whatsloon import WhatsApp
from whatsloon.templates.models import TemplateSpec

ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "YOUR_API_KEY")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "phone_number_id")
WABA_ID = os.environ.get("WHATSAPP_WABA_ID", "waba_id")


def _masked(number: str) -> str:
    """Mask a phone number for display, keeping country context.

    Args:
        number: Display phone number.

    Returns:
        Masked form exposing at most the last four digits.
    """
    digits = "".join(c for c in number if c.isdigit())
    return f"{digits[:2]}••••{digits[-4:]}" if len(digits) > 4 else "••••"


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
    numbers = wa.business.list_phone_numbers(WABA_ID)
    print(f"{len(numbers)} numbers: {[_masked(n.display_phone_number) for n in numbers]}")
    wa.close()


if __name__ == "__main__":
    main()
