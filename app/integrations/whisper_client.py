"""
Whisper Speech-to-Text Client
Uses OpenAI API for high-quality transcription.
"""

import os
import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger("presentos.whisper")

class WhisperClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)

    @classmethod
    def create_from_env(cls) -> Optional["WhisperClient"]:
        key = os.getenv("OPENAI_API_KEY")
        if not key:
            logger.warning("OPENAI_API_KEY not found in .env")
            return None
        return cls(key)

    def transcribe(self, audio_file_path: str) -> str:
        """
        Transcribe an audio file.
        Expects a path to a valid audio file (mp3, mp4, mpeg, mpga, m4a, wav, or webm).
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file,
                    response_format="text"
                )
                return str(transcript).strip()
        except Exception as e:
            logger.error(f"Whisper transcription failed: {e}")
            return ""
