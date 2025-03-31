import requests
import logging
import json
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppService:
    """Service for handling WhatsApp message operations"""

    def __init__(
        self, api_token: str, phone_number_id: str, api_version: str = "v21.0"
    ):
        self.api_token = api_token
        self.phone_number_id = phone_number_id
        self.api_version = api_version
        self.api_url = (
            f"https://graph.facebook.com/{api_version}/{phone_number_id}/messages"
        )

    @staticmethod
    def format_phone_number(phone: str) -> str:
        """Format phone number for WhatsApp API"""
        # Remove any existing prefixes
        phone = phone.replace("whatsapp:", "").strip()

        # Add country code if not present
        if not phone.startswith("+"):
            phone = "+" + phone

        return phone

    def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a message using WhatsApp Business API"""
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json",
        }

        # Format the phone number
        formatted_number = self.format_phone_number(to)
        logger.info(
            f"Attempting to send message to formatted number: {formatted_number}"
        )

        data = {
            "messaging_product": "whatsapp",
            "to": formatted_number,
            "type": "text",
            "text": {"body": message},
        }

        try:
            logger.info(f"Sending WhatsApp message to {formatted_number}")
            logger.info(f"Request URL: {self.api_url}")
            logger.info(f"Request data: {json.dumps(data, indent=2)}")

            response = requests.post(self.api_url, headers=headers, json=data)
            logger.info(f"Response status code: {response.status_code}")
            logger.info(f"Response body: {response.text}")

            if not response.ok:
                logger.error(
                    f"WhatsApp API error: {response.status_code} - {response.text}"
                )
            response.raise_for_status()

            return response.json()
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            raise

    @staticmethod
    def get_media_url(media_id: str, api_token: str, api_version: str) -> Optional[str]:
        """Get media URL from WhatsApp API"""
        try:
            headers = {"Authorization": f"Bearer {api_token}"}
            response = requests.get(
                f"https://graph.facebook.com/{api_version}/{media_id}",
                headers=headers,
            )
            response.raise_for_status()
            return response.json().get("url")
        except Exception as e:
            logger.error(f"Error getting media URL: {str(e)}")
            return None

    @staticmethod
    def download_media(url: str, api_token: str) -> Optional[bytes]:
        """Download media content from WhatsApp URL"""
        try:
            headers = {"Authorization": f"Bearer {api_token}"}
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"Error downloading media: {str(e)}")
            return None
