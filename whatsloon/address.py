"""
Module for sending address messages via WhatsApp Cloud API.

This module defines the AddressSender class, which provides methods to
build payloads and send address messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict
import requests
import httpx
import logging


class AddressSender:
    """
    Mixin class for sending address (interactive) messages via WhatsApp Cloud API.

    Address messages are interactive messages that contain four main parts: header, body, footer, and action. The action component specifies the name "address_message" and relevant parameters.

    Typical workflow:
        1. Business sends an address message with the action name "address_message" to the user.
        2. User interacts with the message by clicking the CTA, fills out their address, and submits the form.
        3. After submission, the partner receives a webhook notification containing the address details.

    Attributes:
        logger (logging.Logger): Logger for WhatsApp address message events.
    """

    logger = logging.getLogger("whatsapp")

    def _build_address_payload(
        self,
        body: str,
        country_iso_code: str,
        header: str = None,
        footer: str = None,
        values: dict = None,
        validation_errors: dict = None,
        saved_addresses: list = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending an address (interactive) message.

        Args:
            body (str): Body text for the address message.
            country_iso_code (str): ISO country code for the address message (e.g., 'IN', 'US').
            header (str, optional): Header text for the address message.
            footer (str, optional): Footer text for the address message.
            values (dict, optional): Pre-filled address values for the form (e.g., name, phone_number, address, etc.).
            validation_errors (dict, optional): Validation errors for specific fields (e.g., {"in_pin_code": "Invalid pin code"}).
            saved_addresses (list, optional): List of saved addresses to show as options.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        parameters = {"country": country_iso_code}
        if values:
            parameters["values"] = values
        if validation_errors:
            parameters["validation_errors"] = validation_errors
        if saved_addresses:
            parameters["saved_addresses"] = saved_addresses

        action = {
            "name": "address_message",
            "parameters": parameters,
        }

        interactive = {
            "type": "address_message",
            "body": {"text": body},
            "action": action,
        }
        if header:
            interactive["header"] = {"type": "text", "text": header}
        if footer:
            interactive["footer"] = {"type": "text", "text": footer}

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

    def send_address_message(
        self,
        body: str,
        country_iso_code: str,
        header: str = None,
        footer: str = None,
        values: dict = None,
        validation_errors: dict = None,
        saved_addresses: list = None,
    ) -> Dict[str, Any]:
        """
        Send an address (interactive) message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            body (str): Body text for the address message.
            country_iso_code (str): ISO country code for the address message (e.g., 'IN', 'US').
            header (str, optional): Header text for the address message.
            footer (str, optional): Footer text for the address message.
            values (dict, optional): Pre-filled address values for the form.
            validation_errors (dict, optional): Validation errors for specific fields.
            saved_addresses (list, optional): List of saved addresses to show as options.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_address_payload(
            body=body,
            country_iso_code=country_iso_code,
            header=header,
            footer=footer,
            values=values,
            validation_errors=validation_errors,
            saved_addresses=saved_addresses,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Address message sent to: {self.recipient_to_send}")
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

    async def async_send_address_message(
        self,
        body: str,
        country_iso_code: str,
        header: str = None,
        footer: str = None,
        values: dict = None,
        validation_errors: dict = None,
        saved_addresses: list = None,
    ) -> Dict[str, Any]:
        """
        Send an address (interactive) message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            body (str): Body text for the address message.
            country_iso_code (str): ISO country code for the address message (e.g., 'IN', 'US').
            header (str, optional): Header text for the address message.
            footer (str, optional): Footer text for the address message.
            values (dict, optional): Pre-filled address values for the form.
            validation_errors (dict, optional): Validation errors for specific fields.
            saved_addresses (list, optional): List of saved addresses to show as options.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_address_payload(
            body=body,
            country_iso_code=country_iso_code,
            header=header,
            footer=footer,
            values=values,
            validation_errors=validation_errors,
            saved_addresses=saved_addresses,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Address message sent to: {self.recipient_to_send}")
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
