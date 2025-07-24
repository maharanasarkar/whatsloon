"""
Module for sending image messages via WhatsApp Cloud API.

This module defines the ImageSender class, which provides methods to build payloads and send image messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, Optional
import requests
import httpx
import logging


class ImageSender:
    """
    Mixin class for sending image messages via WhatsApp Cloud API.

    Supports sending images using either a previously uploaded media ID or a direct media link, with optional caption.
    """

    logger = logging.getLogger("whatsapp")

    def _build_image_payload(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending an image message.

        Args:
            media_id (str, optional): The media ID of the uploaded image.
            media_link (str, optional): The direct link to the image (not recommended).
            caption (str, optional): The caption to display with the image.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        image_obj = {}
        if media_id:
            image_obj["id"] = media_id
        if media_link:
            image_obj["link"] = media_link
        if caption:
            image_obj["caption"] = caption
        if not image_obj:
            raise ValueError("Either media_id or media_link must be provided.")

        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "image",
            "image": image_obj,
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

    def send_image_message(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an image message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            media_id (str, optional): The media ID of the uploaded image.
            media_link (str, optional): The direct link to the image (not recommended).
            caption (str, optional): The caption to display with the image.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_image_payload(
            media_id=media_id,
            media_link=media_link,
            caption=caption,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Image message sent to: {self.recipient_to_send}")
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

    async def async_send_image_message(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an image message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            media_id (str, optional): The media ID of the uploaded image.
            media_link (str, optional): The direct link to the image (not recommended).
            caption (str, optional): The caption to display with the image.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_image_payload(
            media_id=media_id,
            media_link=media_link,
            caption=caption,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Image message sent to: {self.recipient_to_send}")
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
