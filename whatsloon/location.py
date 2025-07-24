"""
Module for sending location messages via WhatsApp Cloud API.

This module defines the LocationSender class, which provides methods to build payloads and send location messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, Optional
import requests
import httpx
import logging


class LocationSender:
    """
    Mixin class for sending location messages via WhatsApp Cloud API.

    Supports sending messages with latitude, longitude, and optional name and address.
    """

    logger = logging.getLogger("whatsapp")

    def _build_location_payload(
        self,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending a location message.

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            name (str, optional): Name of the location. Example: 'Philz Coffee'.
            address (str, optional): Address of the location. Example: '101 Forest Ave, Palo Alto, CA 94301'.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        Raises:
            ValueError: If latitude or longitude are not valid.
        """
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90.")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180.")
        location = {
            "latitude": latitude,
            "longitude": longitude,
        }
        if name:
            location["name"] = name
        if address:
            location["address"] = address
        return {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": self.recipient_to_send,
            "type": "location",
            "location": location,
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

    def send_location_message(
        self,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a location message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            name (str, optional): Name of the location. Example: 'Philz Coffee'.
            address (str, optional): Address of the location. Example: '101 Forest Ave, Palo Alto, CA 94301'.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> client.send_location_message(
            ...     latitude=37.44216251868683,
            ...     longitude=-122.16153582049394,
            ...     name="Philz Coffee",
            ...     address="101 Forest Ave, Palo Alto, CA 94301"
            ... )
        """
        payload = self._build_location_payload(
            latitude=latitude,
            longitude=longitude,
            name=name,
            address=address,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Location message sent to: {self.recipient_to_send}")
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

    async def async_send_location_message(
        self,
        latitude: float,
        longitude: float,
        name: Optional[str] = None,
        address: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Send a location message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            latitude (float): Latitude of the location.
            longitude (float): Longitude of the location.
            name (str, optional): Name of the location. Example: 'Philz Coffee'.
            address (str, optional): Address of the location. Example: '101 Forest Ave, Palo Alto, CA 94301'.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).

        Example:
            >>> await client.async_send_location_message(
            ...     latitude=37.44216251868683,
            ...     longitude=-122.16153582049394,
            ...     name="Philz Coffee",
            ...     address="101 Forest Ave, Palo Alto, CA 94301"
            ... )
        """
        payload = self._build_location_payload(
            latitude=latitude,
            longitude=longitude,
            name=name,
            address=address,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Location message sent to: {self.recipient_to_send}")
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

