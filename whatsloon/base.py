class WhatsAppBaseClient:
    """
    A user-friendly Python wrapper for the WhatsApp Cloud API.

    This class provides a base client for interacting with the WhatsApp Cloud 
    API, allowing you to send messages and manage recipients easily.

    Attributes:
        access_token (str): Access token for the WhatsApp Cloud API.
        mobile_number_id (str): Phone number ID for the WhatsApp Cloud API.
        recipient_mobile_number (str): Recipient's mobile number.
        recipient_to_send (str): Full recipient number including country code.
        country_code (str): Country code of the recipient.
        api_version (str): Version of the WhatsApp Cloud API to use.
        base_url (str): Base URL for the WhatsApp Cloud API endpoint.
        headers (dict): HTTP headers for API requests.
    """

    def __init__(
        self,
        access_token: str,
        mobile_number_id: str,
        recipient_country_code: str,
        recipient_mobile_number: str,
        api_version: str = "v19.0",
    ):
        """
        Initializes a WhatsAppBaseClient instance.

        Args:
            access_token (str): Access token for the WhatsApp Cloud API.
            mobile_number_id (str): Phone number ID for the WhatsApp Cloud API.
            recipient_country_code (str): Country code of the recipient (e.g., '91' for India).
            recipient_mobile_number (str): Recipient's mobile number (without country code).
            api_version (str, optional): Version of the WhatsApp Cloud API to use. Defaults to "v19.0".
        """
        self.access_token = access_token
        self.mobile_number_id = mobile_number_id
        self.recipient_mobile_number = recipient_mobile_number
        self.recipient_to_send = recipient_country_code + recipient_mobile_number
        self.country_code = recipient_country_code
        self.api_version = api_version
        self.base_url = (
            f"https://graph.facebook.com/{self.api_version}/{mobile_number_id}/messages"
        )
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
