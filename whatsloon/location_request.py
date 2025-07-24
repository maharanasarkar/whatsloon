"""
Module for sending location request messages via WhatsApp Cloud API.

This module defines the LocationRequestSender class, which provides methods to build payloads and send location request messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict
import requests
import httpx
import logging


class LocationRequestSender:
    """
    Mixin class for sending location request messages via WhatsApp Cloud API.

    Supports sending interactive messages that prompt the user to share their location.
    """

    logger = logging.getLogger("whatsapp")

    def _build_location_request_payload(
        self,
        body_text: str,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a location request message.

        Args:
            body_text (str): The main body text for the message. Example: "Let's start with your pickup. You can either manually enter an address or share your current location."

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        interactive = {
            "type": "location_request_message",
            "body": {"text": body_text},
            "action": {"name": "send_location"},
        }
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

    def send_location_request_message(
        self,
        body_text: str,
    ) -> Dict[str, Any]:
        """
        Send a location request message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            body_text (str): The main body text for the message. Example: "Let's start with your pickup. You can either manually enter an address or share your current location."

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.send_location_request_message(
            ...     body_text="Let's start with your pickup. You can either manually enter an address or share your current location."
            ... )
        """
        payload = self._build_location_request_payload(body_text=body_text)
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Location request message sent to: {self.recipient_to_send}")
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

    async def async_send_location_request_message(
        self,
        body_text: str,
    ) -> Dict[str, Any]:
        """
        Send a location request message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            body_text (str): The main body text for the message. Example: "Let's start with your pickup. You can either manually enter an address or share your current location."

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_location_request_message(
            ...     body_text="Let's start with your pickup. You can either manually enter an address or share your current location."
            ... )
        """
        payload = self._build_location_request_payload(body_text=body_text)
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Location request message sent to: {self.recipient_to_send}")
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

