import os

from whatsloon import WhatsAppCloudAPIClient

client = WhatsAppCloudAPIClient(
    access_token=os.environ["ACCESS_TOKEN"],
    phone_number_id=os.environ["PHONE_NUMBER_ID"],
    recipient_country_code=os.environ.get("RECIPIENT_COUNTRY_CODE", "91"),
    recipient_mobile_number=os.environ["RECIPIENT_MOBILE_NUMBER"],
)

result = client.send_text_message("Hello from whatsloon!")
print(result)
