"""
Telegram Bot API Client
See: https://core.telegram.org/bots/api

Capabilities:
- Send messages (text, markdown)
- Poll updates (get_updates)
- Webhook management
"""

import os
import logging
import requests
from typing import Dict, Any, Optional, List, Union

logger = logging.getLogger("presentos.telegram_client")

TELEGRAM_API_BASE = "https://api.telegram.org/bot"

class TelegramClient:
    def __init__(self, token: str, default_chat_id: Optional[str] = None):
        self.token = token
        self.base_url = f"{TELEGRAM_API_BASE}{token}"
        self.default_chat_id = default_chat_id or os.getenv("TELEGRAM_CHAT_ID")

    @classmethod
    def create_from_env(cls) -> Optional["TelegramClient"]:
        token = os.getenv("TELEGRAM_BOT_TOKEN")
        if not token:
            logger.warning("TELEGRAM_BOT_TOKEN not found in .env")
            return None
        return cls(token)

    def _post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute POST request to Telegram API"""
        url = f"{self.base_url}/{endpoint}"
        try:
            resp = requests.post(url, json=data, timeout=10)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Telegram API error ({endpoint}): {e}")
            if e.response is not None:
                 logger.error(f"Response: {e.response.text}")
            return {"ok": False, "error": str(e)}

    def send_message(self, text: str, chat_id: Optional[str] = None, parse_mode: str = "Markdown") -> Dict[str, Any]:
        """Send a text message"""
        target_id = chat_id or self.default_chat_id
        if not target_id:
            logger.error("No chat_id provided for Telegram message")
            return {"ok": False, "error": "no_chat_id"}

        payload = {
            "chat_id": target_id,
            "text": text,
            "parse_mode": parse_mode
        }
        return self._post("sendMessage", payload)

    def get_updates(self, offset: Optional[int] = None, timeout: int = 0) -> List[Dict[str, Any]]:
        """Poll for new messages"""
        payload = {
            "timeout": timeout,
            "allowed_updates": ["message"]
        }
        if offset:
            payload["offset"] = offset

        res = self._post("getUpdates", payload)
        if res.get("ok"):
            return res.get("result", [])
        return []

    def get_me(self) -> Dict[str, Any]:
        """Check bot status"""
        return self._post("getMe", {})
