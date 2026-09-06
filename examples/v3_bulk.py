"""Bulk campaign send with pacing and breaker guards."""

import os

from whatsloon import WhatsApp
from whatsloon.messages.models import OutboundMessage, TextMessage
from whatsloon.reliability import BulkSender, CircuitBreaker, RateLimiter

ACCESS_TOKEN = os.environ.get("WHATSAPP_ACCESS_TOKEN", "YOUR_API_KEY")
PHONE_NUMBER_ID = os.environ.get("WHATSAPP_PHONE_NUMBER_ID", "phone_number_id")
RECIPIENTS = os.environ.get("WHATSAPP_TO_LIST", "919876543210").split(",")


def main() -> None:
    """Send one message per recipient with per-item outcomes."""
    wa = WhatsApp(access_token=ACCESS_TOKEN, phone_number_id=PHONE_NUMBER_ID)
    sender = BulkSender(
        wa.messages,
        max_workers=5,
        limiter=RateLimiter(rate_per_second=20.0, capacity=20),
        breaker=CircuitBreaker(failure_threshold=5, cooldown_seconds=30.0),
    )
    envelopes = [
        OutboundMessage(to=to.strip(), content=TextMessage(body="Hello from whatsloon!"))
        for to in RECIPIENTS
        if to.strip()
    ]
    summary = sender.send_all(envelopes)
    print(f"sent={summary.sent} failed={summary.failed}")
    for item in summary.items:
        if not item.ok:
            print(f"{item.to}: {item.error}")
    wa.close()


if __name__ == "__main__":
    main()
