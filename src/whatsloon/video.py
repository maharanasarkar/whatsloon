"""
Module for sending video messages via WhatsApp Cloud API.

This module defines the VideoSender class, which provides methods to build payloads and send video messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, Optional
import requests
import httpx
import logging


class VideoSender:
    """
    Mixin class for sending video messages via WhatsApp Cloud API.

    Supports sending video messages using a media ID (recommended) or a direct link, with optional caption.
    """

    logger = logging.getLogger("whatsapp")

    def _build_video_payload(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a video message.

        Args:
            media_id (str, optional): The ID of the uploaded video media (recommended).
            media_link (str, optional): The direct link to the video media.
            caption (str, optional): Caption for the video.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        Raises:
            ValueError: If neither media_id nor media_link is provided.
        """
        if not media_id and not media_link:
            raise ValueError("You must provide either a media_id or a media_link for the video.")
        video = {}
        if media_id:
            video["id"] = media_id
        if media_link:
            video["link"] = media_link
        if caption:
            video["caption"] = caption
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "video",
            "video": video,
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

    def send_video_message(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a video message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            media_id (str, optional): The ID of the uploaded video media (recommended).
            media_link (str, optional): The direct link to the video media.
            caption (str, optional): Caption for the video.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.send_video_message(media_id="1166846181421424", caption="A succulent eclipse!")
        """
        payload = self._build_video_payload(media_id=media_id, media_link=media_link, caption=caption)
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Video message sent to: {self.recipient_to_send}")
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

    async def async_send_video_message(
        self,
        media_id: Optional[str] = None,
        media_link: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a video message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            media_id (str, optional): The ID of the uploaded video media (recommended).
            media_link (str, optional): The direct link to the video media.
            caption (str, optional): Caption for the video.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_video_message(media_id="1166846181421424", caption="A succulent eclipse!")
        """
        payload = self._build_video_payload(media_id=media_id, media_link=media_link, caption=caption)
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Video message sent to: {self.recipient_to_send}")
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

