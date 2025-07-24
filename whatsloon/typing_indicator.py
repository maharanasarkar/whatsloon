
"""
Mixin class for sending typing indicators via WhatsApp Cloud API.
Implements both synchronous and asynchronous methods.
"""

from typing import Dict, Any
import requests
import httpx
import logging

class TypingIndicator:
    """
    Mixin class for sending typing indicators (on/off) via WhatsApp Cloud API.

    Provides both synchronous and asynchronous methods to send typing indicators.
    """
    logger = logging.getLogger("whatsapp")

    def _build_typing_indicator_payload(self, status: str) -> Dict[str, Any]:
        """
        Build the payload for sending a typing indicator.

        Args:
            status (str): Either 'typing' or 'paused'.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        if status not in ("typing", "paused"):
            raise ValueError("status must be either 'typing' or 'paused'")
        return {
            "messaging_product": "whatsapp",
            "to": self.recipient_to_send,
            "type": "typing",
            "typing": {"status": status},
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

    def send_typing_indicator(self, status: str) -> Dict[str, Any]:
        """
        Send a typing indicator to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            status (str): Either 'typing' (show typing) or 'paused' (hide typing).

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.send_typing_indicator("typing")
            >>> client.send_typing_indicator("paused")
        """
        payload = self._build_typing_indicator_payload(status)
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Typing indicator '{status}' sent to: {self.recipient_to_send}")
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

    async def async_send_typing_indicator(self, status: str) -> Dict[str, Any]:
        """
        Send a typing indicator to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            status (str): Either 'typing' (show typing) or 'paused' (hide typing).

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_typing_indicator("typing")
            >>> await client.async_send_typing_indicator("paused")
        """
        payload = self._build_typing_indicator_payload(status)
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Typing indicator '{status}' sent to: {self.recipient_to_send}")
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
