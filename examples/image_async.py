import asyncio
import os

from whatsloon import WhatsAppCloudAPIClient


async def main():
    client = WhatsAppCloudAPIClient(
        access_token=os.environ["ACCESS_TOKEN"],
        phone_number_id=os.environ["PHONE_NUMBER_ID"],
        recipient_country_code=os.environ.get("RECIPIENT_COUNTRY_CODE", "91"),
        recipient_mobile_number=os.environ["RECIPIENT_MOBILE_NUMBER"],
    )
    result = await client.async_send_image_message(
        media_link="https://example.com/image.jpg",
        caption="Hello with image!",
    )
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
