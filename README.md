# whatsloon

## Overview:
whatsloon is a Python package that simplifies the process of integrating WhatsApp messaging functionality into applications using the WhatsApp Business API. With Whatsloon, developers can easily send various types of messages via WhatsApp, including text messages, multimedia messages, interactive messages, and more.

## Features:
- Send Text Messages: Send plain text messages to WhatsApp recipients.
- Send Multimedia Messages:  Send multimedia messages such as images, videos, audio files, and documents.
- Send Interactive Messages:  Send interactive messages with buttons, lists, product catalogs, and quick replies.
- Handle Message Status:  Receive and handle message status updates, such as message delivery and read receipts.
- Customizable Templates:  Easily create and send messages using customizable templates for consistent branding and messaging.

## Key Components:
- API Integration:  Integrate seamlessly with the WhatsApp Business API to send and receive messages.
- Message Templating:  Use pre-defined message templates or create custom templates for consistent messaging.
- Error Handling:  Handle errors gracefully with built-in error handling and logging capabilities.
- Flexible Configuration:  Configure message parameters such as recipient phone numbers, message content, and message types.

## Installation:
```
pip install whatsloon
```

## Usage Example:
```
from whatsloon.message import WhatsAppClient

# Initialize WhatsApp client
client = WhatsAppClient(
    access_token="YOUR_API_KEY", 
    mobile_number_id="MOBILE_NUMBER_ID",
    country_code="RECIPIENT_COUNTRY_CODE",
    recipient_mobile_number="RECIPIENT_MOBILE_NUMBER",
    )

# Send a text message
response = client.send_text_message(message_text="Hello, world!")

# Check response
print(response)

```