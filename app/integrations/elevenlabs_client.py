"""
ElevenLabs Text-to-Speech Client
Generates high-quality AI voice synthesis.
"""

import os
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("presentos.elevenlabs")

class ElevenLabsClient:
    def __init__(self, api_key: str, voice_id: str = "21m00Tcm4TlvDq8ikWAM"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"

    @classmethod
    def create_from_env(cls) -> Optional["ElevenLabsClient"]:
        key = os.getenv("ELEVENLABS_API_KEY")
        voice_id = os.getenv("ELEVENLABS_VOICE_ID", "21m00Tcm4TlvDq8ikWAM") # Default to Rachel
        if not key:
            logger.warning("ELEVENLABS_API_KEY not found in .env")
            return None
        return cls(key, voice_id)

    def list_voices(self) -> Dict[str, Any]:
        """List available voices to verify API Key"""
        headers = {"xi-api-key": self.api_key}
        url = "https://api.elevenlabs.io/v1/voices"
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.error(f"Failed to list voices: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Body: {e.response.text}")
            return {"error": str(e)}

    def synthesize(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech.
        Returns bytes of the MP3 audio.
        """
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }

        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }

        try:
            response = requests.post(self.base_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            return response.content
        except Exception as e:
            logger.error(f"ElevenLabs synthesis failed: {e}")
            return None
