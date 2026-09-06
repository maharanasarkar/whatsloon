"""
Module for sending text messages via WhatsApp Cloud API.

This module defines the TextSender class, which provides methods to
build payloads and send text messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict
import requests
import httpx
import logging


class TextSender:
    """
    Mixin class for sending text messages via WhatsApp Cloud API.

    Provides methods to construct the payload and send text messages to
    recipients using the WhatsApp Cloud API.
    """

    logger = logging.getLogger("whatsapp")

    def _build_text_payload(
        self, message_text: str, preview_url: bool = True
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a text message.

        Args:
            message_text (str): The text message to send.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API
            request.
        """
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "text",
            "text": {"preview_url": preview_url, "body": message_text},
        }

    def _send_request(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Send a POST request to the WhatsApp Cloud API.

        Args:
            payload (Dict[str, Any]): The payload to send in the request.

        Returns:
            requests.Response: The response object from the API.
        """
        return requests.post(
            url=self.base_url, headers=self.headers, json=payload, timeout=10
        )
    async def _async_send_request(self, payload: Dict[str, Any]) -> httpx.Response:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.base_url, headers=self.headers, json=payload, timeout=10
            )
            return response

    def send_text_message(
        self, message_text: str, preview_url: bool = True
    ) -> Dict[str, Any]:
        """
        Send a text message to the recipient via WhatsApp Cloud API.

        Args:
            message_text (str): The text message to send.
            preview_url (bool, optional): Whether to enable link preview in the message. Defaults to True.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_text_payload(
            message_text, 
            preview_url=preview_url
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Message sent to: {self.recipient_to_send}")
            return {"success": True, "data": response.json()}
        except requests.HTTPError as http_err:
            err_msg = (
                f"{http_err.response.status_code} - {http_err.response.text}"
                if http_err.response
                else str(http_err)
            )
            self.logger.error(f"HTTP error occurred: {err_msg}")
            return {"success": False, "error": err_msg}
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            return {"success": False, "error": str(err)}
    async def async_send_text_message(self, message_text: str, preview_url: bool = True) -> Dict[str, Any]:
        """
        Send a text message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            message_text (str): The text message to send.
            preview_url (bool, optional): Whether to enable link preview in the message. Defaults to True.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_text_payload(message_text, preview_url=preview_url)
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Message sent to: {self.recipient_to_send}")
            return {"success": True, "data": response.json()}
        except httpx.HTTPStatusError as http_err:
            err_msg = (
                f"{http_err.response.status_code} - {http_err.response.text}"
                if http_err.response
                else str(http_err)
            )
            self.logger.error(f"HTTP error occurred: {err_msg}")
            return {"success": False, "error": err_msg}
        except Exception as err:
            self.logger.error(f"An error occurred: {err}")
            return {"success": False, "error": str(err)}
