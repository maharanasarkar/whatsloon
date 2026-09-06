"""Typed v3 messaging across every sender type."""

import os

from whatsloon import WhatsApp
from whatsloon.messages.builders import ButtonsBuilder, ListBuilder
from whatsloon.messages.models import OutboundMessage, TextMessage

ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "YOUR_API_KEY")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "phone_number_id")
TO = os.environ.get("WHATSAPP_TO", "919876543210")


def main() -> None:
    """Send typed messages over the v3 client."""
    wa = WhatsApp(access_token=ACCESS_TOKEN, phone_number_id=PHONE_NUMBER_ID)
    print(wa.messages.send_text(to=TO, body="Hello from whatsloon v3!").message_id)
    print(
        wa.messages.send(
            OutboundMessage(to=TO, content=TextMessage(body="Replying!", preview_url=False))
        ).message_id
    )
    menu = ListBuilder("Pick one", "Menu").section("s", [{"id": "1", "title": "One"}]).build()
    print(wa.messages.send_list(to=TO, content=menu).message_id)
    buttons = ButtonsBuilder("Confirm?").button("yes", "Yes").button("no", "No").build()
    print(wa.messages.send_reply_buttons(to=TO, content=buttons).message_id)
    wa.close()


if __name__ == "__main__":
    main()
