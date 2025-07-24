"""
Module for marking messages as read via WhatsApp Cloud API.

This module defines the ReadMark class, which provides methods to build payloads and mark messages as read using the WhatsApp Cloud API.
"""

from typing import Any, Dict
import requests
import httpx
import logging


class ReadMark:
    """
    Mixin class for marking messages as read via WhatsApp Cloud API.

    Supports marking a message as read using its message ID.
    """

    logger = logging.getLogger("whatsapp")

    def _build_read_payload(
        self,
        message_id: str,
    ) -> Dict[str, Any]:
        """
        Build the payload for marking a message as read.

        Args:
            message_id (str): The ID of the message to mark as read.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        return {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
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

    def mark_message_as_read(
        self,
        message_id: str,
    ) -> Dict[str, Any]:
        """
        Mark a message as read via WhatsApp Cloud API (synchronous).

        Args:
            message_id (str): The ID of the message to mark as read.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.mark_message_as_read(message_id="wamid.HBgLMTY1MDM4Nzk0MzkVAgARGBJDQjZCMzlEQUE4OTJBMTE4RTUA")
        """
        payload = self._build_read_payload(message_id=message_id)
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Marked message as read: {message_id}")
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

    async def async_mark_message_as_read(
        self,
        message_id: str,
    ) -> Dict[str, Any]:
        """
        Mark a message as read via WhatsApp Cloud API (asynchronous).

        Args:
            message_id (str): The ID of the message to mark as read.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_mark_message_as_read(message_id="wamid.HBgLMTY1MDM4Nzk0MzkVAgARGBJDQjZCMzlEQUE4OTJBMTE4RTUA")
        """
        payload = self._build_read_payload(message_id=message_id)
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Marked message as read: {message_id}")
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

