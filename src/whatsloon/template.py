"""
Module for sending template messages via WhatsApp Cloud API.

This module defines the TemplateSender class, which provides methods to build payloads and send template messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, List, Optional
import requests
import httpx
import logging


class TemplateSender:
    """
    Mixin class for sending template messages via WhatsApp Cloud API.

    Supports sending text, media, interactive, and location-based template messages.
    """

    logger = logging.getLogger("whatsapp")

    def _build_template_payload(
        self,
        template_name: str,
        language_code: str,
        components: Optional[List[Dict[str, Any]]] = None,
        recipient_type: str = "individual",
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a template message.

        Args:
            template_name (str): The name of the approved template.
            language_code (str): The language and locale code (e.g., 'en_US').
            components (list, optional): List of template components (header, body, button, etc.).
            recipient_type (str, optional): Recipient type. Defaults to 'individual'.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        template = {
            "name": template_name,
            "language": {"code": language_code},
        }
        if components:
            template["components"] = components
        return {
            "messaging_product": "whatsapp",
            "recipient_type": recipient_type,
            "to": self.recipient_to_send,
            "type": "template",
            "template": template,
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

    def send_template_message(
        self,
        template_name: str,
        language_code: str,
        components: Optional[List[Dict[str, Any]]] = None,
        recipient_type: str = "individual",
    ) -> Dict[str, Any]:
        """
        Send a template message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            template_name (str): The name of the approved template.
            language_code (str): The language and locale code (e.g., 'en_US').
            components (list, optional): List of template components (header, body, button, etc.).
            recipient_type (str, optional): Recipient type. Defaults to 'individual'.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.send_template_message(
            ...     template_name="order_delivery_update",
            ...     language_code="en_US",
            ...     components=[
            ...         {"type": "body", "parameters": [
            ...             {"type": "text", "text": "Pablo"},
            ...             {"type": "text", "text": "566701"}
            ...         ]}
            ...     ]
            ... )
        """
        payload = self._build_template_payload(
            template_name=template_name,
            language_code=language_code,
            components=components,
            recipient_type=recipient_type,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Template message sent to: {self.recipient_to_send}")
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

    async def async_send_template_message(
        self,
        template_name: str,
        language_code: str,
        components: Optional[List[Dict[str, Any]]] = None,
        recipient_type: str = "individual",
    ) -> Dict[str, Any]:
        """
        Send a template message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            template_name (str): The name of the approved template.
            language_code (str): The language and locale code (e.g., 'en_US').
            components (list, optional): List of template components (header, body, button, etc.).
            recipient_type (str, optional): Recipient type. Defaults to 'individual'.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_template_message(
            ...     template_name="order_delivery_update",
            ...     language_code="en_US",
            ...     components=[
            ...         {"type": "body", "parameters": [
            ...             {"type": "text", "text": "Pablo"},
            ...             {"type": "text", "text": "566701"}
            ...         ]}
            ...     ]
            ... )
        """
        payload = self._build_template_payload(
            template_name=template_name,
            language_code=language_code,
            components=components,
            recipient_type=recipient_type,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Template message sent to: {self.recipient_to_send}")
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

