"""
Module for sending interactive Reply Button messages via WhatsApp Cloud API.

This module defines the ReplyButtonSender class, which provides methods to build payloads and send interactive reply button messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, List, Optional
import requests
import httpx
import logging


class ReplyButtonSender:
    """
    Mixin class for sending interactive Reply Button messages via WhatsApp Cloud API.

    Supports sending messages with up to three quick-reply buttons, including header, body, footer, and button definitions.
    """

    logger = logging.getLogger("whatsapp")

    def _build_reply_buttons_payload(
        self,
        body_text: str,
        buttons: List[Dict[str, Any]],
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending an interactive Reply Button message.

        Args:
            body_text (str): The main body text for the message.
            buttons (List[Dict[str, Any]]): List of button dicts, each with 'type' and 'reply' (with 'id' and 'title').
            header (dict, optional): Header for the message. Can be one of:
                - {"type": "text", "text": ...}
                - {"type": "image", "image": {"id": ...} or {"link": ...}}
                - {"type": "video", "video": {"id": ...} or {"link": ...}}
                - {"type": "document", "document": {"id": ...} or {"link": ...}}
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        Raises:
            ValueError: If any API limits are exceeded or header type is invalid.
        """
        # WhatsApp API limits:
        # - Up to 3 buttons
        # - Button title: 20 characters max
        # - Header type: text, image, video, document
        if not (1 <= len(buttons) <= 3):
            raise ValueError("You must provide 1 to 3 reply buttons.")
        for btn in buttons:
            title = btn.get("reply", {}).get("title", "")
            if len(title) > 20:
                raise ValueError("Each button title must be 20 characters or fewer.")
        if header:
            allowed_types = {"text", "image", "video", "document"}
            header_type = header.get("type")
            if header_type not in allowed_types:
                raise ValueError(f"Header type must be one of {allowed_types}.")
        interactive = {
            "type": "button",
            "body": {"text": body_text},
            "action": {
                "buttons": buttons,
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

    def send_reply_buttons_message(
        self,
        body_text: str,
        buttons: List[Dict[str, Any]],
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive Reply Button message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            body_text (str): The main body text for the message.
            buttons (List[Dict[str, Any]]): List of button dicts, each with 'type' and 'reply' (with 'id' and 'title').
            header (dict, optional): Header for the message (text, image, etc.).
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_reply_buttons_payload(
            body_text=body_text,
            buttons=buttons,
            header=header,
            footer_text=footer_text,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Reply buttons message sent to: {self.recipient_to_send}")
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

    async def async_send_reply_buttons_message(
        self,
        body_text: str,
        buttons: List[Dict[str, Any]],
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive Reply Button message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            body_text (str): The main body text for the message.
            buttons (List[Dict[str, Any]]): List of button dicts, each with 'type' and 'reply' (with 'id' and 'title').
            header (dict, optional): Header for the message (text, image, etc.).
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_reply_buttons_payload(
            body_text=body_text,
            buttons=buttons,
            header=header,
            footer_text=footer_text,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Reply buttons message sent to: {self.recipient_to_send}")
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

