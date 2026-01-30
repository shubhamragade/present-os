"""
Murf AI Text-to-Speech Client
Generates high-quality AI voice synthesis using Murf.ai API.
"""

import os
import requests
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger("presentos.murf")

class MurfClient:
    def __init__(self, api_key: str, voice_id: str = "en-US-marcus"):
        self.api_key = api_key
        self.voice_id = voice_id
        self.base_url = "https://api.murf.ai/v1/speech/generate-with-key"

    @classmethod
    def create_from_env(cls) -> Optional["MurfClient"]:
        key = os.getenv("MURF_API_KEY")
        voice_id = os.getenv("MURF_VOICE_ID", "en-US-marcus")
        if not key:
            logger.warning("MURF_API_KEY not found in .env")
            return None
        return cls(key, voice_id)

    def synthesize(self, text: str) -> Optional[bytes]:
        """
        Convert text to speech using Murf.ai REST API.
        Returns bytes of the audio file (Murf returns a download URL or direct content depending on endpoint).
        For /generate-with-key it usually returns a JSON with an audioUrl.
        """
        headers = {
            "Content-Type": "application/json",
            "api-key": self.api_key
        }

        data = {
            "voiceId": self.voice_id,
            "text": text[:1000],  # Murf has a 1000 char limit per request
            "format": "MP3"
        }

        try:
            logger.info(f"Synthesizing speech with Murf (voiceId={self.voice_id})")
            response = requests.post(self.base_url, json=data, headers=headers, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            # Murf API returns 'audioFile' not 'audioUrl'
            audio_url = result.get("audioFile") or result.get("audioUrl")
            
            if not audio_url:
                logger.error(f"Murf response missing audioFile/audioUrl: {result}")
                return None
                
            # Download the actual audio content
            audio_resp = requests.get(audio_url, timeout=30)
            audio_resp.raise_for_status()
            return audio_resp.content

        except Exception as e:
            logger.error(f"Murf synthesis failed: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"Error body: {e.response.text}")
            return None
