"""
Module for sending interactive Flow messages via WhatsApp Cloud API.

This module defines the FlowSender class, which provides methods to build payloads and send interactive flow messages using the WhatsApp Cloud API.
"""

from typing import Any, Dict, Optional
import requests
import httpx
import logging


class FlowSender:
    """
    Mixin class for sending interactive Flow messages via WhatsApp Cloud API.

    Supports sending messages with WhatsApp Flows, including header, body, footer, and action parameters.
    """

    logger = logging.getLogger("whatsapp")

    def _build_flow_payload(
        self,
        flow_token: str,
        flow_id: str,
        flow_cta: str,
        flow_action: str,
        flow_message_version: str = "3",
        body_text: Optional[str] = None,
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
        flow_action_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build the payload for sending an interactive Flow message.

        Args:
            flow_token (str): The flow token for the WhatsApp Flow.
            flow_id (str): The flow ID.
            flow_cta (str): The call-to-action button text.
            flow_action (str): The flow action (e.g., 'navigate').
            flow_message_version (str, optional): The flow message version. Defaults to "3".
            body_text (str, optional): The main body text for the message.
            header (dict, optional): Header for the message (text, image, etc.).
            footer_text (str, optional): Footer text for the message.
            flow_action_payload (dict, optional): Additional payload for the flow action.

        Returns:
            Dict[str, Any]: The payload dictionary for the WhatsApp API request.
        """
        interactive = {
            "type": "flow",
            "action": {
                "name": "flow",
                "parameters": {
                    "flow_message_version": flow_message_version,
                    "flow_token": flow_token,
                    "flow_id": flow_id,
                    "flow_cta": flow_cta,
                    "flow_action": flow_action,
                },
            },
        }
        if body_text:
            interactive["body"] = {"text": body_text}
        if header:
            interactive["header"] = header
        if footer_text:
            interactive["footer"] = {"text": footer_text}
        if flow_action_payload:
            interactive["action"]["parameters"]["flow_action_payload"] = flow_action_payload

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

    def send_flow_message(
        self,
        flow_token: str,
        flow_id: str,
        flow_cta: str,
        flow_action: str,
        flow_message_version: str = "3",
        body_text: Optional[str] = None,
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
        flow_action_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive Flow message to the recipient via WhatsApp Cloud API (synchronous).

        Args:
            flow_token (str): The flow token for the WhatsApp Flow.
            flow_id (str): The flow ID.
            flow_cta (str): The call-to-action button text.
            flow_action (str): The flow action (e.g., 'navigate').
            flow_message_version (str, optional): The flow message version. Defaults to "3".
            body_text (str, optional): The main body text for the message.
            header (dict, optional): Header for the message (text, image, etc.).
            footer_text (str, optional): Footer text for the message.
            flow_action_payload (dict, optional): Additional payload for the flow action.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_flow_payload(
            flow_token=flow_token,
            flow_id=flow_id,
            flow_cta=flow_cta,
            flow_action=flow_action,
            flow_message_version=flow_message_version,
            body_text=body_text,
            header=header,
            footer_text=footer_text,
            flow_action_payload=flow_action_payload,
        )
        try:
            response = self._send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Flow message sent to: {self.recipient_to_send}")
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

    async def async_send_flow_message(
        self,
        flow_token: str,
        flow_id: str,
        flow_cta: str,
        flow_action: str,
        flow_message_version: str = "3",
        body_text: Optional[str] = None,
        header: Optional[Dict[str, Any]] = None,
        footer_text: Optional[str] = None,
        flow_action_payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Send an interactive Flow message to the recipient via WhatsApp Cloud API (asynchronous).

        Args:
            flow_token (str): The flow token for the WhatsApp Flow.
            flow_id (str): The flow ID.
            flow_cta (str): The call-to-action button text.
            flow_action (str): The flow action (e.g., 'navigate').
            flow_message_version (str, optional): The flow message version. Defaults to "3".
            body_text (str, optional): The main body text for the message.
            header (dict, optional): Header for the message (text, image, etc.).
            footer_text (str, optional): Footer text for the message.
            flow_action_payload (dict, optional): Additional payload for the flow action.

        Returns:
            Dict[str, Any]: A dictionary with the result of the operation. Contains 'success' (bool), and either 'data' (dict) or 'error' (str).
        """
        payload = self._build_flow_payload(
            flow_token=flow_token,
            flow_id=flow_id,
            flow_cta=flow_cta,
            flow_action=flow_action,
            flow_message_version=flow_message_version,
            body_text=body_text,
            header=header,
            footer_text=footer_text,
            flow_action_payload=flow_action_payload,
        )
        try:
            response = await self._async_send_request(payload)
            response.raise_for_status()
            self.logger.info(f"Flow message sent to: {self.recipient_to_send}")
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

