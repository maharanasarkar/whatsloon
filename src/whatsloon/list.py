"""
Module for sending interactive List messages via WhatsApp Cloud API.

This module defines the ListSender class, which provides methods to build payloads and send interactive list messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, List, Optional
import requests
import httpx
import logging


class ListSender:
    """
    Mixin class for sending interactive List messages via WhatsApp Cloud API.

    Supports sending messages with a list of options, including header, body, footer, button, and sections.
    """

    logger = logging.getLogger("whatsapp")

    def _build_list_payload(
        self,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending an interactive List message.

        Args:
            body_text (str): The main body text for the message.
            button_text (str): The text to display on the list button.
            sections (List[Dict[str, Any]]): List of section dicts, each with 'title' and 'rows'.
            header (dict, optional): Header for the message (text, image, etc.).
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        Raises:
            ValueError: If any API limits are exceeded.
        """
        # WhatsApp API limits:
        # - button_text: 20 characters max
        # - up to 10 sections
        # - up to 10 rows total (across all sections)
        if len(button_text) > 20:
            raise ValueError("Button text must be 20 characters or fewer.")
        if len(sections) > 10:
            raise ValueError("You can have at most 10 sections in a list message.")
        total_rows = sum(len(section.get("rows", [])) for section in sections)
        if total_rows > 10:
            raise ValueError("You can have at most 10 rows in total across all sections.")

        interactive = {
            "type": "list",
            "body": {"text": body_text},
            "action": {
                "button": button_text,
                "sections": sections,
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

    def send_list_message(
        self,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive List message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            body_text (str): The main body text for the message.
            button_text (str): The text to display on the list button.
            sections (List[Dict[str, Any]]): List of section dicts, each with 'title' and 'rows'.
            header (dict, optional): Header for the message (text, image, etc.).
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_list_payload(
            body_text=body_text,
            button_text=button_text,
            sections=sections,
            header=header,
            footer_text=footer_text,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"List message sent to: {self.recipient_to_send}")
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

    async def async_send_list_message(
        self,
        body_text: str,
        button_text: str,
        sections: List[Dict[str, Any]],
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive List message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            body_text (str): The main body text for the message.
            button_text (str): The text to display on the list button.
            sections (List[Dict[str, Any]]): List of section dicts, each with 'title' and 'rows'.
            header (dict, optional): Header for the message (text, image, etc.).
            footer_text (str, optional): Footer text for the message.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_list_payload(
            body_text=body_text,
            button_text=button_text,
            sections=sections,
            header=header,
            footer_text=footer_text,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"List message sent to: {self.recipient_to_send}")
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

