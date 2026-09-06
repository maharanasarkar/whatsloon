"""Group messaging and voice call handling."""

import os

from whatsloon import WhatsApp
from whatsloon.groups.models import GroupCreate
from whatsloon.messages.models import OutboundMessage, TextMessage

ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "YOUR_API_KEY")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "phone_number_id")


def main() -> None:
    """Create a group, message it, and place a call."""
    wa = WhatsApp(access_token=ACCESS_TOKEN, phone_number_id=PHONE_NUMBER_ID)
    group = wa.groups.create_group(GroupCreate(subject="Team"))
    print(group.id, group.invite_link)
    print(
        wa.messages.send(
            OutboundMessage(
                to=group.id, content=TextMessage(body="Welcome!"), recipient_type="group"
            )
        ).message_id
    )
    print(wa.calls.get_settings())
    wa.close()


if __name__ == "__main__":
    main()
