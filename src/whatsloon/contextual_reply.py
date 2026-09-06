"""
Module for sending contextual reply messages via WhatsApp Cloud API.

This module defines the ContextualReply class, which provides methods to build payloads and send contextual reply messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, Optional
import requests
import httpx
import logging


class ContextualReply:
    """
    Mixin class for sending contextual reply messages via WhatsApp Cloud API.

    Supports sending a message as a reply to a previous message using its message ID.
    """

    logger = logging.getLogger("whatsapp")

    def _build_contextual_reply_payload(
        self,
        reply_to_message_id: str,
        message_type: str,
        message_content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a contextual reply message.
        Raises TypeError if required arguments are missing.
        """
        if not reply_to_message_id:
            raise TypeError("reply_to_message_id is required")
        if not message_type:
            raise TypeError("message_type is required")
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "context": {"message_id": reply_to_message_id},
            "type": message_type,
            message_type: message_content,
        }
        return payload

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

    def send_contextual_reply(
        self,
        reply_to_message_id: str,
        message_type: str,
        message_content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send a contextual reply message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            reply_to_message_id (str): The ID of the message to reply to.
            message_type (str): The type of message to send (e.g., 'text', 'image', etc.).
            message_content (dict): The content of the message (e.g., for text: {"body": "..."}).

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.send_contextual_reply(
            ...     reply_to_message_id="wamid.HBgLMTY0NjcwNDM1OTUVAgASGBQzQTdCNTg5RjY1MEMyRjlGMjRGNgA=",
            ...     message_type="text",
            ...     message_content={"body": "You're welcome, Pablo!"}
            ... )
        """
        payload = self._build_contextual_reply_payload(
            reply_to_message_id=reply_to_message_id,
            message_type=message_type,
            message_content=message_content,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Contextual reply sent to: {self.recipient_to_send}")
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

    async def async_send_contextual_reply(
        self,
        reply_to_message_id: str,
        message_type: str,
        message_content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Send a contextual reply message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            reply_to_message_id (str): The ID of the message to reply to.
            message_type (str): The type of message to send (e.g., 'text', 'image', etc.).
            message_content (dict): The content of the message (e.g., for text: {"body": "..."}).

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_contextual_reply(
            ...     reply_to_message_id="wamid.HBgLMTY0NjcwNDM1OTUVAgASGBQzQTdCNTg5RjY1MEMyRjlGMjRGNgA=",
            ...     message_type="text",
            ...     message_content={"body": "You're welcome, Pablo!"}
            ... )
        """
        payload = self._build_contextual_reply_payload(
            reply_to_message_id=reply_to_message_id,
            message_type=message_type,
            message_content=message_content,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Contextual reply sent to: {self.recipient_to_send}")
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

