import re
from typing import Optional


class WhatsAppBaseClient:
    """
    A user-friendly Python wrapper for the WhatsApp Cloud API.

    This class provides a base client for interacting with the WhatsApp Cloud
    API, allowing you to send messages and manage recipients easily.

    Attributes:
        access_token (str): Access token for the WhatsApp Cloud API.
        phone_number_id (str): Phone number ID for the WhatsApp Cloud API.
        recipient_phone_number (str): Recipient's phone number.
        recipient_to_send (str): Full recipient number including country code.
        country_code (str): Country code of the recipient.
        api_version (str): Version of the WhatsApp Cloud API to use.
        base_url (str): Base URL for the WhatsApp Cloud API endpoint.
        headers (dict): HTTP headers for API requests.
    """

    COUNTRY_CODE_PATTERN = re.compile(r"^\+?\d{1,4}$")
    MOBILE_NUMBER_PATTERN = re.compile(r"^\+?\d{6,15}$")

    def __init__(
        self,
        access_token: str,
        phone_number_id: str,
        recipient_mobile_number: str,
        recipient_country_code: Optional[str] = None,
        api_version: str = "v19.0",
    ):
        """
        Initializes a WhatsAppBaseClient instance with proper validation and normalization.

        Args:
            access_token (str): Access token for authenticating with the WhatsApp Cloud API.
            phone_number_id (str): The ID of the phone number registered with the WhatsApp Cloud API.
            recipient_mobile_number (str): The recipient's mobile number (with or without country code).
            recipient_country_code (Optional[str], optional): The country code (e.g., '91' for India).
                If provided, it will be prepended to the recipient's mobile number. If omitted,
                the mobile number must already be in international format.
            api_version (str, optional): The version of the WhatsApp Cloud API to use. Defaults to "v19.0".

        Raises:
            ValueError: If any required argument is missing, empty, or does not meet formatting criteria.
            TypeError: If arguments are not of the expected type.
        """

        for name, val in [
            ("access_token", access_token),
            ("phone_number_id", phone_number_id),
            ("recipient_mobile_number", recipient_mobile_number),
            ("api_version", api_version),
        ]:
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"{name} must be a non-empty string.")

        if recipient_country_code is not None:
            if not isinstance(recipient_country_code, str):
                raise TypeError("recipient_country_code must be a string or None.")
            if not self.COUNTRY_CODE_PATTERN.fullmatch(recipient_country_code.strip()):
                raise ValueError(
                    "recipient_country_code must be 1–4 digits, optionally prefixed with '+'."
                )
            recipient_country_code = recipient_country_code.strip().lstrip("+")
        recipient_mobile_number = recipient_mobile_number.strip().lstrip("+")
        if not recipient_mobile_number.isdigit() or not (
            6 <= len(recipient_mobile_number) <= 15
        ):
            raise ValueError(
                "recipient_mobile_number must be 6–15 digits, optionally prefixed with '+'."
            )

        self.access_token = access_token.strip()
        self.phone_number_id = phone_number_id.strip()
        self.recipient_mobile_number = recipient_mobile_number
        self.country_code = recipient_country_code

        self.recipient_to_send = (
            f"{recipient_country_code}{recipient_mobile_number}"
            if recipient_country_code
            else recipient_mobile_number
        )

        self.api_version = api_version.strip()
        self.base_url = f"https://graph.facebook.com/{self.api_version}/{self.phone_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def __repr__(self):
        return (
            f"<WhatsAppBaseClient to={self.recipient_to_send} "
            f"version={self.api_version}>"
        )
