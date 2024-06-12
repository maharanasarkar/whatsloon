import requests
from typing import Dict, Any, Optional, List
import logging

logging.basicConfig(
    level=logging.INFO,                  
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    filename='app.log',
    filemode='w'
)

logger = logging.getLogger(__name__)

class WhatsAppCloudAPI:
    """
    A simple Python wrapper for the WhatsApp Cloud API.

    Attributes:
        access_token (str): The access token for the WhatsApp Cloud API.
        mobile_number_id (str): The phone number ID for the WhatsApp Cloud API.
        base_url (str): The base URL for the WhatsApp Cloud API.
    """

    def __init__(
        self,
        access_token: str,
        country_code: str,
        mobile_number_id: str,
        recipient_mobile_number: str,
    ):
        """
        Initialize the WhatsAppCloudAPI with the provided access token and phone number ID.

        Args:
            access_token (str): Your access token for the WhatsApp Cloud API.
            mobile_number_id (str): Your phone number ID for the WhatsApp Cloud API.
        """
        self.access_token = access_token
        self.mobile_number_id = mobile_number_id
        self.recipient_mobile_number = recipient_mobile_number
        self.recipient_to_send = country_code + recipient_mobile_number
        self.country_code = country_code
        self.base_url = f"https://graph.facebook.com/v19.0/{mobile_number_id}/messages"
        self.headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }

    def send_text_message(self, message_text: str) -> Dict[str, Any]:
        """
        Send a message using the WhatsApp Cloud API.

        Args:
            message_text (str): The message text to send.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "text",
            "text": {"preview_url": False, "body": message_text},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(f"Message sent to : {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_text_message(
        self, message_text: str, message_id: str
    ) -> Dict[str, Any]:
        """
        Send a reply to a text message using the WhatsApp Cloud API.

        Args:
            message_text (str): The reply message text to send.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "text",
            "text": {"preview_url": False, "body": message_text},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(f"Reply sent to : {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_text_message_with_preview_url(self, message_text: str) -> Dict[str, Any]:
        """
        Send a text message with URL preview using the WhatsApp Cloud API.

        Args:
            message_text (str): The message text including a URL to send.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "text",
            "text": {"preview_url": True, "body": message_text},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(f"Message with preview URL sent to : {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_with_reaction_message(
        self, message_id: str, emoji: str
    ) -> Dict[str, Any]:
        """
        Send a reaction to a specific message using the WhatsApp Cloud API.

        Args:
            message_id (str): The ID of the message to react to.
            emoji (str): The emoji to use for the reaction.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "reaction",
            "reaction": {"message_id": message_id, "emoji": emoji},
        }
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Reaction '{emoji}' sent to message ID: {message_id}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}
        return response.json()


    def send_image_message_by_id(self, image_object_id: str) -> Dict[str, Any]:
        """
        Send an image message using the WhatsApp Cloud API by providing the image object ID.

        Args:
            image_object_id (str): The ID of the image object to send.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "image",
            "image": {"id": image_object_id},
        }

        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(
                f"Image message sent to : {self.recipient_to_send} with image object ID: {image_object_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_image_message(
        self, message_id: str, image_id: str
    ) -> Dict[str, Any]:
        """
        Send a reply to an image message using the WhatsApp Cloud API.

        Args:
            message_id (str): The ID of the message to reply to.
            image_id (str): The ID of the image to send.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "image",
            "image": {"id": image_id},
        }

        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Image reply sent to : {self.recipient_to_send} with image ID: {image_id} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_image_message_by_url(self, image_url: str) -> Dict[str, Any]:
        """
        Send an image message using the WhatsApp Cloud API by providing the image URL.

        Args:
            image_url (str): The URL of the image to send.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "image",
            "image": {"link": image_url},
        }

        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Image message sent to : {self.recipient_to_send} with image URL: {image_url}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_image_message_by_url(
        self, message_id: str, image_url: str
    ) -> Dict[str, Any]:
        """
        Send a reply message to an Image using the WhatsApp Cloud API by providing the Image URL.

        Args:
            message_id (str): The ID of the message to reply to.
            image_url (str): The URL of the image to send.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.

        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "image",
            "image": {"link": image_url},
        }

        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Image reply sent to: {self.recipient_to_send} with image URL: {image_url} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_audio_message_by_id(self, audio_id: str) -> Dict[str, Any]:
        """
        Send an audio message using the WhatsApp Cloud API by providing the audio ID.

        Args:
            audio_id (str): The ID of the audio to send.
            recipient_mobile_number (str): The recipient's phone number.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "audio",
            "audio": {"id": audio_id},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Audio message sent to : {self.recipient_to_send} with audio object ID: {audio_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_audio_message_by_id(
        self, message_id: str, audio_id: str
    ) -> Dict[str, Any]:
        """
        Send a reply to a message with an audio message using the WhatsApp Cloud API by providing the audio object ID.

        Args:
            message_id (str): The ID of the message to reply to.
            audio_id (str): The ID of the audio object to send.
            recipient_mobile_number (str): The recipient's phone number.

        Returns:
            Dict[str, Any]: The response from the WhatsApp Cloud API.

        Raises:
            requests.HTTPError: If an HTTP error occurs.
            Exception: If any other exception occurs.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "audio",
            "audio": {"id": audio_id},
        }
        try:
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(
                f"Audio reply sent to: {self.recipient_to_send} with audio ID: {audio_id} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_audio_message_by_url(self, audio_url: str) -> Dict[str, Any]:
        """
        Send an audio message via WhatsApp by specifying a URL to the audio file.

        Args:
            audio_url (str): The URL of the audio file to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "audio",
            "audio": {"link": audio_url},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Audio message sent to : {self.recipient_to_send} with audio object ID: {audio_url}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_audio_message_by_url(
        self, message_id: str, audio_url: str
    ) -> Dict[str, Any]:
        """
        Send an audio message reply via WhatsApp in response to a specific message by specifying the message ID and a URL to the audio file.

        Args:
            message_id (str): The ID of the message to which this reply is being sent.
            audio_url (str): The URL of the audio file to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "{{Recipient-Phone-Number}}",
            "context": {"message_id": message_id},
            "type": "audio",
            "audio": {"link": audio_url},
        }

        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Audio reply sent to: {self.recipient_to_send} with audio ID: {audio_url} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_document_message_by_id(
        self, document_id: str, document_caption: str, document_filename: str
    ) -> Dict[str, Any]:
        """
        Send a document message via WhatsApp by specifying the document ID, caption, and filename.

        Args:
            document_id (str): The ID of the document to be sent.
            document_caption (str): The caption for the document.
            document_filename (str): The filename for the document.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "document",
            "document": {
                "id": document_id,
                "caption": document_caption,
                "filename": document_filename,
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Document message sent to: {self.recipient_to_send} with document ID: {document_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_document_message_by_id(
        self,
        message_id: str,
        document_id: str,
        document_caption: str,
        document_filename: str,
    ) -> Dict[str, Any]:
        """
        Send a document message reply via WhatsApp in response to a specific message by specifying the message ID,
        document ID, caption, and filename.

        Args:
            message_id (str): The ID of the message to which this reply is being sent.
            document_id (str): The ID of the document to be sent.
            document_caption (str): The caption for the document.
            document_filename (str): The filename for the document.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "document",
            "document": {
                "id": document_id,
                "caption": document_caption,
                "filename": document_filename,
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Document reply sent to: {self.recipient_to_send} with document ID: {document_id} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_document_message_by_url(
        self, document_url: str, document_caption: str
    ) -> Dict[str, Any]:
        """
        Send a document message via WhatsApp by specifying a URL to the document and a caption.

        Args:
            document_url (str): The URL of the document to be sent.
            document_caption (str): The caption for the document.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "document",
            "document": {
                "link": document_url,
                "caption": document_caption,
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Document message sent to: {self.recipient_to_send} with document URL: {document_url}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_document_by_url(
        self, message_id: str, document_url: str, document_caption: str
    ) -> Dict[str, Any]:
        """
        Send a document message reply via WhatsApp in response to a specific message by specifying the message ID,
        document URL, and caption.

        Args:
            message_id (str): The ID of the message to which this reply is being sent.
            document_url (str): The URL of the document to be sent.
            document_caption (str): The caption for the document.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "document",
            "document": {
                "link": document_url,
                "caption": document_caption,
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Document reply sent to: {self.recipient_to_send} with document URL: {document_url} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_sticker_message_by_id(self, sticker_id: str) -> Dict[str, Any]:
        """
        Send a sticker message via WhatsApp by specifying the sticker ID.

        Args:
            sticker_id (str): The ID of the sticker to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "sticker",
            "sticker": {"id": sticker_id},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Sticker message sent to: {self.recipient_to_send} with sticker ID: {sticker_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_sticker_message_by_id(
        self, message_id: str, sticker_id: str
    ) -> Dict[str, Any]:
        """
        Send a sticker message reply via WhatsApp in response to a specific message by specifying the message ID
        and sticker ID.

        Args:
            message_id (str): The ID of the message to which this reply is being sent.
            sticker_id (str): The ID of the sticker to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "sticker",
            "sticker": {"id": sticker_id},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Sticker reply sent to: {self.recipient_to_send} with sticker ID: {sticker_id} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_sticker_message_by_url(self, sticker_url: str) -> Dict[str, Any]:
        """
        Send a sticker message via WhatsApp by specifying the URL of the sticker.

        Args:
            sticker_url (str): The URL of the sticker to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "sticker",
            "sticker": {"link": sticker_url},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Sticker message sent to: {self.recipient_to_send} with sticker URL: {sticker_url}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_sticker_message_by_url(
        self, message_id: str, sticker_url: str
    ) -> Dict[str, Any]:
        """
        Send a sticker message reply via WhatsApp in response to a specific message by specifying the message ID
        and sticker URL.

        Args:
            message_id (str): The ID of the message to which this reply is being sent.
            sticker_url (str): The URL of the sticker to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "sticker",
            "sticker": {"link": sticker_url},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Sticker reply sent to: {self.recipient_to_send} with sticker URL: {sticker_url} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_video_message_by_id(
        self, video_caption: str, video_id: str
    ) -> Dict[str, Any]:
        """
        Send a video message via WhatsApp by specifying the video caption and ID.

        Args:
            video_caption (str): The caption for the video.
            video_id (str): The ID of the video to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "{{Recipient-Phone-Number}}",
            "type": "video",
            "video": {"caption": video_caption, "id": video_id},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Video message sent to: {self.recipient_to_send} with video ID: {video_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_video_message_by_id(
        self, message_id: str, video_caption: str, video_id: str
    ) -> Dict[str, Any]:
        """
        Send a video message reply via WhatsApp in response to a specific message by specifying the message ID,
        video caption, and ID.

        Args:
            message_id (str): The ID of the message to which this reply is being sent.
            video_caption (str): The caption for the video.
            video_id (str): The ID of the video to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "video",
            "video": {"caption": video_caption, "id": video_id},
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Video reply sent to: {self.recipient_to_send} with video ID: {video_id} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_video_message_by_url(
        self, video_caption: str, video_url: str
    ) -> Dict[str, Any]:
        """
        Send a video message via WhatsApp by specifying the video caption and URL.

        Args:
            video_caption (str): The caption for the video.
            video_url (str): The URL of the video to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "video",
            "video": {
                "link": video_url,
                "caption": video_caption,
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Video message sent to: {self.recipient_to_send} with video URL: {video_url}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_video_message_by_url(
        self, message_id: str, video_caption: str, video_url: str
    ) -> Dict[str, Any]:
        """
        Send a video message reply via WhatsApp in response to a specific message by specifying the message ID,
        video caption, and URL.

        Args:
            message_id (str): The ID of the message to which this reply is being sent.
            video_caption (str): The caption for the video.
            video_url (str): The URL of the video to be sent.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "video",
            "video": {
                "link": video_url,
                "caption": video_caption,
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Video reply sent to: {self.recipient_to_send} with video URL: {video_url} in response to message ID: {message_id}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_contact_message(
        self,
        formatted_name: str,
        first_name: str = "",
        last_name: str = "",
        middle_name: str = "",
        suffix: str = "",
        prefix: str = "",
        email: str = "",
        org_company: str = "",
        org_department: str = "",
        org_title: str = "",
        phone: str = "",
        wa_id: str = "",
        url: str = "",
        address_street: str = "",
        address_city: str = "",
        address_state: str = "",
        address_zip: str = "",
        address_country: str = "",
        address_country_code: str = "",
        birthday: str = "",
    ) -> Dict[str, Any]:
        """
        Send a contact message via WhatsApp.

        Args:
            formatted_name (str): The formatted name of the contact (required).
            first_name (str): The first name of the contact.
            last_name (str): The last name of the contact.
            middle_name (str): The middle name of the contact.
            suffix (str): The suffix of the contact.
            prefix (str): The prefix of the contact.
            email (str): The email of the contact.
            org_company (str): The company of the contact's organization.
            org_department (str): The department of the contact's organization.
            org_title (str): The title of the contact's organization.
            phone (str): The phone number of the contact.
            wa_id (str): The WhatsApp ID of the contact.
            url (str): The URL of the contact.
            address_street (str): The street address of the contact.
            address_city (str): The city of the contact's address.
            address_state (str): The state of the contact's address.
            address_zip (str): The ZIP code of the contact's address.
            address_country (str): The country of the contact's address.
            address_country_code (str): The country code of the contact's address.
            birthday (str): The birthday of the contact.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": self.recipient_to_send,
            "type": "contacts",
            "contacts": [
                {
                    "name": {
                        "formatted_name": formatted_name,
                        "first_name": first_name,
                        "last_name": last_name,
                        "middle_name": middle_name,
                        "suffix": suffix,
                        "prefix": prefix,
                    },
                    "emails": [{"email": email, "type": "WORK"}] if email else [],
                    "org": {
                        "company": org_company,
                        "department": org_department,
                        "title": org_title,
                    },
                    "phones": [{"phone": phone, "wa_id": wa_id, "type": "WORK"}] if phone else [],
                    "urls": [{"url": url, "type": "WORK"}] if url else [],
                    "addresses": [
                        {
                            "street": address_street,
                            "city": address_city,
                            "state": address_state,
                            "zip": address_zip,
                            "country": address_country,
                            "country_code": address_country_code,
                            "type": "WORK"
                        }
                    ] if address_street else [],
                    "birthday": birthday,
                }
            ],
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(f"Contact message sent to: {self.recipient_to_send}.")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_contact_message(
        self,
        message_id: str,
        formatted_name: str,
        first_name: str = "",
        last_name: str = "",
        middle_name: str = "",
        suffix: str = "",
        prefix: str = "",
        email: str = "",
        org_company: str = "",
        org_department: str = "",
        org_title: str = "",
        phone: str = "",
        wa_id: str = "",
        url: str = "",
        address_street: str = "",
        address_city: str = "",
        address_state: str = "",
        address_zip: str = "",
        address_country: str = "",
        address_country_code: str = "",
        birthday: str = "",
    ) -> Dict[str, Any]:
        """
        Send a contact message reply via WhatsApp in response to a previous message.

        Args:
            formatted_name (str): The formatted name of the contact (required).
            first_name (str): The first name of the contact.
            last_name (str): The last name of the contact.
            middle_name (str): The middle name of the contact.
            suffix (str): The suffix of the contact.
            prefix (str): The prefix of the contact.
            email (str): The email of the contact.
            org_company (str): The company of the contact's organization.
            org_department (str): The department of the contact's organization.
            org_title (str): The title of the contact's organization.
            phone (str): The phone number of the contact.
            wa_id (str): The WhatsApp ID of the contact.
            url (str): The URL of the contact.
            address_street (str): The street address of the contact.
            address_city (str): The city of the contact's address.
            address_state (str): The state of the contact's address.
            address_zip (str): The ZIP code of the contact's address.
            address_country (str): The country of the contact's address.
            address_country_code (str): The country code of the contact's address.
            birthday (str): The birthday of the contact.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "contacts",
            "contacts": [
                {
                    "name": {
                        "formatted_name": formatted_name,
                        "first_name": first_name,
                        "last_name": last_name,
                        "middle_name": middle_name,
                        "suffix": suffix,
                        "prefix": prefix,
                    },
                    "emails": [{"email": email, "type": "WORK"}] if email else [],
                    "org": {
                        "company": org_company,
                        "department": org_department,
                        "title": org_title,
                    },
                    "phones": [{"phone": phone, "wa_id": wa_id, "type": "WORK"}] if phone else [],
                    "urls": [{"url": url, "type": "WORK"}] if url else [],
                    "addresses": [
                        {
                            "street": address_street,
                            "city": address_city,
                            "state": address_state,
                            "zip": address_zip,
                            "country": address_country,
                            "country_code": address_country_code,
                            "type": "WORK"
                        }
                    ] if address_street else [],
                    "birthday": birthday,
                }
            ],
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info("Contact message sent.")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_location_message(
        self, latitude: str, longitude: str, name: str, address: str
    ) -> Dict[str, Any]:
        """
        Send a location message via WhatsApp.

        Args:
            latitude (str): The latitude of the location.
            longitude (str): The longitude of the location.
            name (str): The name of the location.
            address (str): The address of the location.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": name,
                "address": address,
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(f"Location message sent to: {self.recipient_to_send}.")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_to_location_message(
        self, message_id: str, latitude: str, longitude: str, name: str, address: str
    ) -> Dict[str, Any]:
        """
        Send a location message reply via WhatsApp in response to a previous message.

        Args:
            message_id (str): The ID of the previous message to which this is a reply.
            latitude (str): The latitude of the location.
            longitude (str): The longitude of the location.
            name (str): The name of the location.
            address (str): The address of the location.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "location",
            "location": {
                "latitude": latitude,
                "longitude": longitude,
                "name": name,
                "address": address,
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(f"Location message reply sent to: {self.recipient_to_send}.")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_message_template_id(
            self,

    ) -> Dict[str, Any]:
        """
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": "{{Recipient-Phone-Number}}",
            "type": "template",
            "template": {
                "name": "template-name",
                "language": {"code": "language-and-locale-code"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": "text-string"},
                            {
                                "type": "currency",
                                "currency": {
                                    "fallback_value": "$100.99",
                                    "code": "USD",
                                    "amount_1000": 100990,
                                },
                            },
                            {
                                "type": "date_time",
                                "date_time": {
                                    "fallback_value": "February 25, 1977",
                                    "day_of_week": 5,
                                    "year": 1977,
                                    "month": 2,
                                    "day_of_month": 25,
                                    "hour": 15,
                                    "minute": 33,
                                    "calendar": "GREGORIAN",
                                },
                            },
                        ],
                    }
                ],
            },
        }
        try:
            response = requests.post(
                url=self.base_url, headers=self.headers, json=payload
            )
            response.raise_for_status()
            logger.info(f"Location message reply sent to: {self.recipient_to_send}.")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_template_message(
        self,
        template_name: str,
        language_code: str,
        message_text: str,
        fallback_currency_value: str = None,
        currency_code: str = None,
        currency_amount: int = None,
        fallback_date_value: str = None,
        day_of_week: int = None,
        year: int = None,
        month: int = None,
        day_of_month: int = None,
        hour: int = None,
        minute: int = None,
        calendar: str = None,
    ) -> Dict[str, Any]:
        """
        Send a message using a template via WhatsApp.

        Args:
        template_name (str): The name of the template to use.
        language_code (str): The language code for the template.
        message_text (str): The text message to send.
        fallback_currency_value (str, optional): Fallback value for the currency parameter.
        currency_code (str, optional): Currency code for the currency parameter.
        currency_amount (int, optional): Amount in the smallest unit (e.g., cents).
        fallback_date_value (str, optional): Fallback value for the date-time parameter.
        day_of_week (int, optional): Day of the week for the date-time parameter.
        year (int, optional): Year for the date-time parameter.
        month (int, optional): Month for the date-time parameter.
        day_of_month (int, optional): Day of the month for the date-time parameter.
        hour (int, optional): Hour for the date-time parameter.
        minute (int, optional): Minute for the date-time parameter.
        calendar (str, optional): Calendar type for the date-time parameter.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": [
                    {
                        "type": "body",
                        "parameters": [{"type": "text", "text": message_text}],
                    }
                ],
            },
        }

        if fallback_currency_value and currency_code and currency_amount:
            payload["template"]["components"][0]["parameters"].append(
                {
                    "type": "currency",
                    "currency": {
                        "fallback_value": fallback_currency_value,
                        "code": currency_code,
                        "amount_1000": currency_amount,
                    },
                }
            )

        if (
            fallback_date_value
            and day_of_week is not None
            and year
            and month
            and day_of_month is not None
            and hour is not None
            and minute is not None
            and calendar
        ):
            payload["template"]["components"][0]["parameters"].append(
                {
                    "type": "date_time",
                    "date_time": {
                        "fallback_value": fallback_date_value,
                        "day_of_week": day_of_week,
                        "year": year,
                        "month": month,
                        "day_of_month": day_of_month,
                        "hour": hour,
                        "minute": minute,
                        "calendar": calendar,
                    },
                }
            )

        try:
            response = requests.post(url=self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(
                f"Template message sent to {self.recipient_to_send} with template: {template_name}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_template_message_with_header(
        self,
        template_name: str,
        language_code: str,
        message_text: str,
        header_image_url: str = None,
        fallback_currency_value: str = None,
        currency_code: str = None,
        currency_amount: int = None,
        fallback_date_value: str = None,
        day_of_week: int = None,
        year: int = None,
        month: int = None,
        day_of_month: int = None,
        hour: int = None,
        minute: int = None,
        calendar: str = None,
    ) -> Dict[str, Any]:
        """
        Send a message using a template via WhatsApp, including a header image and various body parameters.

        Args:
            template_name (str): The name of the template to use.
            language_code (str): The language code for the template.
            message_text (str): The text message to send.
            header_image_url (str, optional): URL of the header image.
            fallback_currency_value (str, optional): Fallback value for the currency parameter.
            currency_code (str, optional): Currency code for the currency parameter.
            currency_amount (int, optional): Amount in the smallest unit (e.g., cents).
            fallback_date_value (str, optional): Fallback value for the date-time parameter.
            day_of_week (int, optional): Day of the week for the date-time parameter.
            year (int, optional): Year for the date-time parameter.
            month (int, optional): Month for the date-time parameter.
            day_of_month (int, optional): Day of the month for the date-time parameter.
            hour (int, optional): Hour for the date-time parameter.
            minute (int, optional): Minute for the date-time parameter.
            calendar (str, optional): Calendar type for the date-time parameter.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": [],
            },
        }

        if header_image_url:
            payload["template"]["components"].append(
                {
                    "type": "header",
                    "parameters": [{"type": "image", "image": {"link": header_image_url}}],
                }
            )

        body_component = {
            "type": "body",
            "parameters": [{"type": "text", "text": message_text}],
        }

        if fallback_currency_value and currency_code and currency_amount:
            body_component["parameters"].append(
                {
                    "type": "currency",
                    "currency": {
                        "fallback_value": fallback_currency_value,
                        "code": currency_code,
                        "amount_1000": currency_amount,
                    },
                }
            )

        if (
            fallback_date_value
            and day_of_week is not None
            and year
            and month
            and day_of_month is not None
            and hour is not None
            and minute is not None
            and calendar
        ):
            body_component["parameters"].append(
                {
                    "type": "date_time",
                    "date_time": {
                        "fallback_value": fallback_date_value,
                        "day_of_week": day_of_week,
                        "year": year,
                        "month": month,
                        "day_of_month": day_of_month,
                        "hour": hour,
                        "minute": minute,
                        "calendar": calendar,
                    },
                }
            )

        payload["template"]["components"].append(body_component)

        try:
            response = requests.post(url=self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(
                f"Template message with header sent to {self.recipient_to_send} with template: {template_name}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_template_message_with_header_and_buttons(
        self, template_name: str, language_code: str, message_text: str,
        header_image_url: str = None, fallback_currency_value: str = None, currency_code: str = None, currency_amount: int = None,
        fallback_date_value: str = None, day_of_week: int = None, year: int = None, month: int = None,
        day_of_month: int = None, hour: int = None, minute: int = None, calendar: str = None,
        button_payloads: list = None
    ) -> Dict[str, Any]:
        """
        Send a message using a template via WhatsApp, including a header image, various body parameters, and quick reply buttons.

        Args:
            template_name (str): The name of the template to use.
            language_code (str): The language code for the template.
            message_text (str): The text message to send.
            header_image_url (str, optional): URL of the header image.
            fallback_currency_value (str, optional): Fallback value for the currency parameter.
            currency_code (str, optional): Currency code for the currency parameter.
            currency_amount (int, optional): Amount in the smallest unit (e.g., cents).
            fallback_date_value (str, optional): Fallback value for the date-time parameter.
            day_of_week (int, optional): Day of the week for the date-time parameter.
            year (int, optional): Year for the date-time parameter.
            month (int, optional): Month for the date-time parameter.
            day_of_month (int, optional): Day of the month for the date-time parameter.
            hour (int, optional): Hour for the date-time parameter.
            minute (int, optional): Minute for the date-time parameter.
            calendar (str, optional): Calendar type for the date-time parameter.
            button_payloads (list, optional): List of payloads for the quick reply buttons.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": []
            },
        }

        if header_image_url:
            payload["template"]["components"].append(
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {
                                "link": header_image_url
                            }
                        }
                    ]
                }
            )

        body_component = {
            "type": "body",
            "parameters": [
                {"type": "text", "text": message_text}
            ]
        }

        if fallback_currency_value and currency_code and currency_amount:
            body_component["parameters"].append(
                {
                    "type": "currency",
                    "currency": {
                        "fallback_value": fallback_currency_value,
                        "code": currency_code,
                        "amount_1000": currency_amount,
                    },
                }
            )

        if (
            fallback_date_value and day_of_week is not None 
            and year and month and day_of_month is not None 
            and hour is not None and minute is not None and calendar
            ):
            body_component["parameters"].append(
                {
                    "type": "date_time",
                    "date_time": {
                        "fallback_value": fallback_date_value,
                        "day_of_week": day_of_week,
                        "year": year,
                        "month": month,
                        "day_of_month": day_of_month,
                        "hour": hour,
                        "minute": minute,
                        "calendar": calendar,
                    },
                }
            )

        payload["template"]["components"].append(body_component)

        if button_payloads:
            for index, payload in enumerate(button_payloads):
                payload["template"]["components"].append(
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": str(index),
                        "parameters": [
                            {
                                "type": "payload",
                                "payload": payload
                            }
                        ]
                    }
                )

        try:
            response = requests.post(
                url=self.base_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(
                f"Template message with header and buttons sent to {self.recipient_to_send} with template: {template_name}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_interactive_list_message(
        self, header_text: str, body_text: str, footer_text: str,
        button_text: str, sections: list
    ) -> Dict[str, Any]:
        """
        Send an interactive list message via WhatsApp.

        Args:
            header_text (str): The text for the message header.
            body_text (str): The text for the message body.
            footer_text (str): The text for the message footer.
            button_text (str): The text for the action button.
            sections (list): A list of sections, each containing a title and rows with id, title, and description.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {
                    "type": "text",
                    "text": header_text
                },
                "body": {
                    "text": body_text
                },
                "footer": {
                    "text": footer_text
                },
                "action": {
                    "button": button_text,
                    "sections": []
                }
            }
        }

        for section in sections:
            section_payload = {
                "title": section.get("title"),
                "rows": []
            }
            for row in section.get("rows", []):
                row_payload = {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "description": row.get("description", "")
                }
                section_payload["rows"].append(row_payload)
            payload["interactive"]["action"]["sections"].append(section_payload)

        try:
            response = requests.post(
                url=self.base_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Interactive list message sent to {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_reply_interactive_list_message(
        self,
        message_id: str,
        header_text: str,
        body_text: str,
        footer_text: str,
        button_text: str,
        sections: list,
    ) -> Dict[str, Any]:
        """
        Send an interactive list message via WhatsApp in reply to a specific message.

        Args:
            message_id (str): The ID of the message being replied to.
            header_text (str): The text for the message header.
            body_text (str): The text for the message body.
            footer_text (str): The text for the message footer.
            button_text (str): The text for the action button.
            sections (list): A list of sections, each containing a title and rows with id, title, and description.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": message_id},
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": header_text},
                "body": {"text": body_text},
                "footer": {"text": footer_text},
                "action": {"button": button_text, "sections": []},
            },
        }

        for section in sections:
            section_payload = {"title": section.get("title"), "rows": []}
            for row in section.get("rows", []):
                row_payload = {
                    "id": row.get("id"),
                    "title": row.get("title"),
                    "description": row.get("description", ""),
                }
                section_payload["rows"].append(row_payload)
            payload["interactive"]["action"]["sections"].append(section_payload)

        try:
            response = requests.post(url=self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Interactive list message reply sent to {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_interactive_button_message(
        self, body_text: str, buttons: list
    ) -> Dict[str, Any]:
        """
        Send an interactive button message via WhatsApp.

        Args:
            body_text (str): The text for the message body.
            buttons (list): A list of buttons object, each containing a unique id and title.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "interactive",
            "interactive": {
                "type": "button",
                "body": {
                    "text": body_text
                },
                "action": {
                    "buttons": []
                }
            }
        }

        for button in buttons:
            button_payload = {
                "type": "reply",
                "reply": {
                    "id": button.get("id"),
                    "title": button.get("title")
                }
            }
            payload["interactive"]["action"]["buttons"].append(button_payload)

        try:
            response = requests.post(
                url=self.base_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Interactive button message sent to {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_message_read_receipt(
        self, incoming_msg_id: str
    ) -> Dict[str, Any]:
        """
        Send a message read receipt via WhatsApp.

        Args:
            incoming_msg_id (str): The ID of the incoming message.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": incoming_msg_id
        }

        try:
            response = requests.post(
                url=self.base_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Read receipt sent for message ID: {incoming_msg_id}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_interactive_product_message(
        self,
        catalog_id: str,
        product_retailer_id: str,
        body_text: Optional[str] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive product message via WhatsApp.

        Args:
            catalog_id (str): The catalog ID.
            product_retailer_id (str): The product retailer ID.
            body_text (Optional[str]): Optional body text.
            footer_text (Optional[str]): Optional footer text.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "interactive",
            "interactive": {
                "type": "product",
                "body": {"text": body_text or ""},
                "footer": {"text": footer_text or ""},
                "action": {
                    "catalog_id": catalog_id,
                    "product_retailer_id": product_retailer_id,
                },
            },
        }

        if not body_text:
            del payload["interactive"]["body"]
        if not footer_text:
            del payload["interactive"]["footer"]

        try:
            response = requests.post(url=self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(f"Interactive product message sent to: {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_interactive_product_list_message(
        self,
        catalog_id: str,
        sections: List[Dict[str, Any]],
        header_type: Optional[str] = None,
        header_text: Optional[str] = None,
        body_text: Optional[str] = None,
        footer_text: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Send an interactive product list message via WhatsApp.

        Args:
            catalog_id (str): The catalog ID.
            sections (List[Dict[str, Any]]): A list of sections with product items.
            header_type (Optional[str]): Optional header type.
            header_text (Optional[str]): Optional header text.
            body_text (Optional[str]): Optional body text.
            footer_text (Optional[str]): Optional footer text.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "interactive",
            "interactive": {
                "type": "product_list",
                "header": {
                    "type": header_type,
                    "text": header_text
                },
                "body": {
                    "text": body_text
                },
                "footer": {
                    "text": footer_text
                },
                "action": {
                    "catalog_id": catalog_id,
                    "sections": sections
                }
            }
        }

        if not header_type or not header_text:
            del payload["interactive"]["header"]
        if not body_text:
            del payload["interactive"]["body"]
        if not footer_text:
            del payload["interactive"]["footer"]

        try:
            response = requests.post(
                url=self.base_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Interactive product list message sent to: {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()

    def send_interactive_catalog_message(
        self,
        thumbnail_product_retailer_id: str,
        body_text: str,
        footer_text: str
    ) -> Dict[str, Any]:
        """
        Send an interactive catalog message via WhatsApp.

        Args:
            thumbnail_product_retailer_id (str): The retailer ID of the thumbnail product.
            body_text (str): The body text of the message.
            footer_text (str): The footer text of the message.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "interactive",
            "interactive": {
                "type": "catalog_message",
                "body": {
                    "text": body_text
                },
                "action": {
                    "name": "catalog_message",
                    "parameters": {
                        "thumbnail_product_retailer_id": thumbnail_product_retailer_id
                    }
                },
                "footer": {
                    "text": footer_text
                }
            }
        }

        try:
            response = requests.post(
                url=self.base_url,
                headers=self.headers,
                json=payload
            )
            response.raise_for_status()
            logger.info(f"Interactive catalog message sent to: {self.recipient_to_send}")
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()


    def send_catalog_offer_template_message(
        self,
        thumbnail_product_retailer_id: str,
        language_code: str = "en_US",
        offer_parameters: List[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a template message with a catalog offer via WhatsApp.

        Args:
            thumbnail_product_retailer_id (str): The retailer ID of the thumbnail product.
            language_code (str, optional): The language code. Defaults to "en_US".
            offer_parameters (List[str], optional): List of offer parameters. Defaults to None.

        Returns:
            Dict[str, Any]: A dictionary containing the response from the server.
            If an error occurs, the dictionary contains an "error" key with the error message.

        Raises:
            requests.HTTPError: If an HTTP error occurs during the request.
            Exception: If a general error occurs during the request.
        """
        if offer_parameters is None:
            offer_parameters = ["100", "400", "3"]

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "template",
            "template": {
                "name": "intro_catalog_offer",
                "language": {"code": language_code},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": offer_parameters[0]},
                            {"type": "text", "text": offer_parameters[1]},
                            {"type": "text", "text": offer_parameters[2]},
                        ],
                    },
                    {
                        "type": "button",
                        "sub_type": "CATALOG",
                        "index": 0,
                        "parameters": [
                            {
                                "type": "action",
                                "action": {
                                    "thumbnail_product_retailer_id": thumbnail_product_retailer_id
                                },
                            }
                        ],
                    },
                ],
            },
        }

        try:
            response = requests.post(url=self.base_url, headers=self.headers, json=payload)
            response.raise_for_status()
            logger.info(
                f"Template message with catalog offer sent to: {self.recipient_to_send}"
            )
        except requests.HTTPError as http_err:
            logger.error(f"HTTP error occurred: {http_err}")
            return {"error": str(http_err)}
        except Exception as err:
            logger.error(f"An error occurred: {err}")
            return {"error": str(err)}

        return response.json()
