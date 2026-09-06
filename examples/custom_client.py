import os

from whatsloon import ImageSender, TextSender, WhatsAppBaseClient


class MyClient(WhatsAppBaseClient, TextSender, ImageSender):
    pass


client = MyClient(
    access_token=os.environ["ACCESS_TOKEN"],
    phone_number_id=os.environ["PHONE_NUMBER_ID"],
    recipient_country_code=os.environ.get("RECIPIENT_COUNTRY_CODE", "91"),
    recipient_mobile_number=os.environ["RECIPIENT_MOBILE_NUMBER"],
)

print(client.send_text_message("Hello from a custom client!"))
