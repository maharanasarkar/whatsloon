"""
Module for sending interactive Call-to-Action (CTA) URL button messages via WhatsApp Cloud API.

This module defines the CTASender class, which provides methods to build payloads and send CTA URL button messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, Optional
import requests
import httpx
import logging


class CTASender:
    """
    Mixin class for sending interactive CTA URL button messages via WhatsApp Cloud API.

    Supports sending messages with a button that opens a URL, with optional header (text, image, video, document), body, and footer.
    """

    logger = logging.getLogger("whatsapp")

    def _build_cta_payload(
        self,
        body_text: str,
        button_text: str,
        button_url: str,
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending an interactive CTA URL button message.

        Args:
            body_text (str): The main body text for the message.
            button_text (str): The text to display on the CTA button.
            button_url (str): The URL to open when the button is clicked.
            header (dict, optional): Header for the message (text, image, video, or document header as per API docs).
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        interactive = {
            "type": "cta_url",
            "body": {"text": body_text},
            "action": {
                "name": "cta_url",
                "parameters": {
                    "display_text": button_text,
                    "url": button_url,
                },
            },
        }
        if header:
            interactive["header"] = header
        if footer_text:
            interactive["footer"] = {"text": footer_text}

        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "interactive",
            "interactive": interactive,
        }

    def _send_request(self, payload: Dict[str, Any]) -> requests.Response:
        """
        Send a POST request to the WhatsApp Cloud API (synchronous).

        Args:
            payload (Dict[str, Any]): The payload to send in the request.

        Returns:
            requests.Response: The response object from the API.
        """
        return requests.post(
            url=self.base_url, headers=self.headers, json=payload, timeout=10
        )

    async def _async_send_request(self, payload: Dict[str, Any]) -> httpx.Response:
        """
        Send a POST request to the WhatsApp Cloud API (asynchronous).

        Args:
            payload (Dict[str, Any]): The payload to send in the request.

        Returns:
            httpx.Response: The response object from the API.
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url=self.base_url, headers=self.headers, json=payload, timeout=10
            )
            return response

    def send_cta_message(
        self,
        body_text: str,
        button_text: str,
        button_url: str,
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive CTA URL button message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            body_text (str): The main body text for the message.
            button_text (str): The text to display on the CTA button.
            button_url (str): The URL to open when the button is clicked.
            header (dict, optional): Header for the message (text, image, video, or document header as per API docs).
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_cta_payload(
            body_text=body_text,
            button_text=button_text,
            button_url=button_url,
            header=header,
            footer_text=footer_text,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"CTA message sent to: {self.recipient_to_send}")
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

    async def async_send_cta_message(
        self,
        body_text: str,
        button_text: str,
        button_url: str,
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive CTA URL button message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            body_text (str): The main body text for the message.
            button_text (str): The text to display on the CTA button.
            button_url (str): The URL to open when the button is clicked.
            header (dict, optional): Header for the message (text, image, video, or document header as per API docs).
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_cta_payload(
            body_text=body_text,
            button_text=button_text,
            button_url=button_url,
            header=header,
            footer_text=footer_text,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"CTA message sent to: {self.recipient_to_send}")
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
