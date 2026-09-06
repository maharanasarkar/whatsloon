"""
Module for sending sticker messages via WhatsApp Cloud API.

This module defines the StickerSender class, which provides methods to build payloads and send sticker messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, Optional
import requests
import httpx
import logging


class StickerSender:
    """
    Mixin class for sending sticker messages via WhatsApp Cloud API.

    Supports sending sticker messages using a media ID (recommended) or a direct link.
    """

    logger = logging.getLogger("whatsapp")

    def _build_sticker_payload(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a sticker message.

        Args:
            media_id (str, optional): The ID of the uploaded sticker media (recommended).
            media_link (str, optional): The direct link to the sticker media (not recommended).

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        Raises:
            ValueError: If neither media_id nor media_link is provided.
        """
        if not media_id and not media_link:
            raise ValueError("You must provide either a media_id or a media_link for the sticker.")
        sticker = {}
        if media_id:
            sticker["id"] = media_id
        if media_link:
            sticker["link"] = media_link
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "sticker",
            "sticker": sticker,
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

    def send_sticker_message(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a sticker message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            media_id (str, optional): The ID of the uploaded sticker media (recommended).
            media_link (str, optional): The direct link to the sticker media (not recommended).

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.send_sticker_message(media_id="798882015472548")
        """
        payload = self._build_sticker_payload(media_id=media_id, media_link=media_link)
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Sticker message sent to: {self.recipient_to_send}")
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

    async def async_send_sticker_message(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a sticker message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            media_id (str, optional): The ID of the uploaded sticker media (recommended).
            media_link (str, optional): The direct link to the sticker media (not recommended).

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_sticker_message(media_id="798882015472548")
        """
        payload = self._build_sticker_payload(media_id=media_id, media_link=media_link)
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Sticker message sent to: {self.recipient_to_send}")
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

