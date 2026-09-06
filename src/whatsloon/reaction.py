"""
Module for sending reaction messages via WhatsApp Cloud API.

This module defines the ReactionSender class, which provides methods to build payloads and send reaction messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict
import requests
import httpx
import logging


class ReactionSender:
    """
    Mixin class for sending reaction messages via WhatsApp Cloud API.

    Supports sending emoji reactions to previously received user messages.
    """

    logger = logging.getLogger("whatsapp")

    def _build_reaction_payload(
        self,
        message_id: str,
        emoji: str,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a reaction message.

        Args:
            message_id (str): The ID of the message to react to.
            emoji (str): The emoji to use as the reaction. Example: "😀"

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "reaction",
            "reaction": {
                "message_id": message_id,
                "emoji": emoji,
            },
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

    def send_reaction_message(
        self,
        message_id: str,
        emoji: str,
    ) -> Dict[str, Any]:
        """
        Send a reaction message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            message_id (str): The ID of the message to react to.
            emoji (str): The emoji to use as the reaction. Example: "😀"

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.send_reaction_message(
            ...     message_id="wamid.HBgLMTY0NjcwNDM1OTUVAgASGBQzQUZCMTY0MDc2MUYwNzBDNTY5MAA=",
            ...     emoji="😀"
            ... )
        """
        payload = self._build_reaction_payload(message_id=message_id, emoji=emoji)
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Reaction message sent to: {self.recipient_to_send}")
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

    async def async_send_reaction_message(
        self,
        message_id: str,
        emoji: str,
    ) -> Dict[str, Any]:
        """
        Send a reaction message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            message_id (str): The ID of the message to react to.
            emoji (str): The emoji to use as the reaction. Example: "😀"

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_reaction_message(
            ...     message_id="wamid.HBgLMTY0NjcwNDM1OTUVAgASGBQzQUZCMTY0MDc2MUYwNzBDNTY5MAA=",
            ...     emoji="😀"
            ... )
        """
        payload = self._build_reaction_payload(message_id=message_id, emoji=emoji)
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Reaction message sent to: {self.recipient_to_send}")
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

