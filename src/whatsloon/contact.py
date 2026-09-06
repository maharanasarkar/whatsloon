"""
Module for sending contact messages via WhatsApp Cloud API.

This module defines the ContactSender class, which provides methods to build payloads and send contact messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, List
import requests
import httpx
import logging


class ContactSender:
    """
    Mixin class for sending contact messages via WhatsApp Cloud API.

    Supports sending rich contact information including names, phone numbers, addresses, emails, organizations, and URLs.
    """

    logger = logging.getLogger("whatsapp")

    def _build_contact_payload(
        self,
        contacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a contact message.

        Args:
            contacts (List[Dict[str, Any]]): List of contact dicts, each following WhatsApp Cloud API contact message structure.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        if not contacts or not isinstance(contacts, list):
            raise ValueError("contacts must be a non-empty list of contact dicts.")

        return {
            "messaging_product": "whatsapp",
            "to": self.recipient_to_send,
            "type": "contacts",
            "contacts": contacts,
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

    def send_contact_message(
        self,
        contacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Send a contact message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            contacts (List[Dict[str, Any]]): List of contact dicts, each following WhatsApp Cloud API contact message structure.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> contact = {
            ...     "name": {
            ...         "formatted_name": "John Doe",
            ...         "first_name": "John",
            ...         "last_name": "Doe"
            ...     },
            ...     "phones": [
            ...         {"phone": "+1234567890", "type": "Mobile", "wa_id": "1234567890"}
            ...     ],
            ...     "emails": [
            ...         {"email": "john.doe@example.com", "type": "Work"}
            ...     ]
            ... }
            >>> client.send_contact_message([contact])
        """
        payload = self._build_contact_payload(contacts)
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Contact message sent to: {self.recipient_to_send}")
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

    async def async_send_contact_message(
        self,
        contacts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Send a contact message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            contacts (List[Dict[str, Any]]): List of contact dicts, each following WhatsApp Cloud API contact message structure.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_contact_message([contact])
        """
        payload = self._build_contact_payload(contacts)
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Contact message sent to: {self.recipient_to_send}")
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
