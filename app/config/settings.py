"""
Central configuration loader for Present OS.
Loads and validates all environment variables used across the system.

Usage:
    from app.config.settings import settings
    token = settings.NOTION_TOKEN
"""

from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv
load_dotenv()  # Load .env from current directory

def _require(name: str) -> str:
    """Fetch an environment variable; crash early if missing."""
    value = os.getenv(name)
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    return value


@dataclass
class Settings:
    # -----------------------------
    # Core App Settings
    # -----------------------------
    ENV: str = os.getenv("ENV", "development")
    APP_BASE_URL: str = os.getenv("APP_BASE_URL", "http://localhost:8000")
    PORT: int = int(os.getenv("PORT", 8000))

    # -----------------------------
    # OPENAI
    # -----------------------------
    OPENAI_API_KEY: str = _require("OPENAI_API_KEY")
    OPENAI_ORG: str = os.getenv("OPENAI_ORG", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_WHISPER_MODEL: str = os.getenv("OPENAI_WHISPER_MODEL", "whisper-1")

    # -----------------------------
    # WEATHER
    # -----------------------------
    WEATHER_API_KEY: str = os.getenv("WEATHER_API_KEY", "")

    # -----------------------------
    # MONARCH / WEALTHFRONT (optional)
    # -----------------------------
    MONARCH_API_KEY: str = os.getenv("MONARCH_API_KEY", "")
    WEALTHFRONT_API_KEY: str = os.getenv("WEALTHFRONT_API_KEY", "")

    # -----------------------------
    # NOTION
    # -----------------------------
    NOTION_TOKEN: str = _require("NOTION_TOKEN")
    NOTION_ROOT_PAGE_ID: str = _require("NOTION_ROOT_PAGE_ID")

    NOTION_DB_TASKS_ID: str = os.getenv("NOTION_DB_TASKS_ID", "")
    NOTION_DB_XP_ID: str = os.getenv("NOTION_DB_XP_ID", "")
    NOTION_DB_CONTACTS_ID: str = os.getenv("NOTION_DB_CONTACTS_ID", "")
    NOTION_DB_QUESTS_ID: str = os.getenv("NOTION_DB_QUESTS_ID", "")
    NOTION_DB_MAPS_ID: str = os.getenv("NOTION_DB_MAPS_ID", "")

    # -----------------------------
    # PINECONE
    # -----------------------------
    PINECONE_API_KEY: str = os.getenv("PINECONE_API_KEY", "")
    PINECONE_INDEX: str = os.getenv("PINECONE_INDEX", "presentos-memory-1536")
    PINECONE_DIM: int = int(os.getenv("PINECONE_DIM", 1536))
    PINECONE_REGION: str = os.getenv("PINECONE_REGION", "")
    PINECONE_HOST: str = os.getenv("PINECONE_HOST", "")
    RAG_NAMESPACE: str = os.getenv("RAG_NAMESPACE", "presentos-rag")

    # -----------------------------
    # GOOGLE OAUTH (Calendar + Gmail)
    # -----------------------------
    GOOGLE_OAUTH_CLIENT_ID: str = os.getenv("GOOGLE_OAUTH_CLIENT_ID", "")
    GOOGLE_OAUTH_CLIENT_SECRET: str = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET", "")
    GOOGLE_OAUTH_REDIRECT_URI: str = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "")
    GMAIL_USER_EMAIL: str = os.getenv("GMAIL_USER_EMAIL", "")
    GMAIL_REFRESH_TOKEN: str = os.getenv("GMAIL_REFRESH_TOKEN", "")
    GMAIL_TOKEN_URI: str = os.getenv("GMAIL_TOKEN_URI", "https://oauth2.googleapis.com/token")

    # -----------------------------
    # FIRELIES (AI meeting agent)
    # -----------------------------
    FIREFLIES_API_KEY: str = os.getenv("FIREFLIES_API_KEY", "")

    # -----------------------------
    # PERPLEXITY
    # -----------------------------
    PERPLEXITY_API_KEY: str = os.getenv("PERPLEXITY_API_KEY", "")

    # -----------------------------
    # ELEVENLABS (TTS)
    # -----------------------------
    ELEVENLABS_API_KEY: str = os.getenv("ELEVENLABS_API_KEY", "")
    ELEVENLABS_VOICE_ID: str = os.getenv("ELEVENLABS_VOICE_ID", "")

    # -----------------------------
    # TELEGRAM BOT
    # -----------------------------
    TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

    # -----------------------------
    # TWILIO (Optional SMS)
    # -----------------------------
    TWILIO_SID: str = os.getenv("TWILIO_SID", "")
    TWILIO_TOKEN: str = os.getenv("TWILIO_TOKEN", "")
    TWILIO_FROM_NUMBER: str = os.getenv("TWILIO_FROM_NUMBER", "")
    USER_PHONE: str = os.getenv("USER_PHONE", "")

    # -----------------------------
    # TIMEZONE
    # -----------------------------
    USER_TIMEZONE: str = os.getenv("USER_TIMEZONE", "Asia/Kolkata")

    # -----------------------------
    # WHOOP (Energy API)
    # -----------------------------
    WHOOP_CLIENT_ID: str = os.getenv("WHOOP_CLIENT_ID", "")
    WHOOP_CLIENT_SECRET: str = os.getenv("WHOOP_CLIENT_SECRET", "")
    WHOOP_REDIRECT_URI: str = os.getenv("WHOOP_REDIRECT_URI", "")
    WHOOP_ACCESS_TOKEN: str = os.getenv("WHOOP_ACCESS_TOKEN", "")
    WHOOP_USER_ID: str = os.getenv("WHOOP_USER_ID", "")

    # -----------------------------
    # Deployment toggles
    # -----------------------------
    USE_PINECONE: bool = os.getenv("USE_PINECONE", "false").lower() == "true"
    USE_NOTION: bool = os.getenv("USE_NOTION", "true").lower() == "true"
    USE_FIREFLIES: bool = os.getenv("USE_FIREFLIES", "false").lower() == "true"
    USE_ELEVENLABS: bool = os.getenv("USE_ELEVENLABS", "false").lower() == "true"

    # -----------------------------
    # Logging / Sentry
    # -----------------------------
    SENTRY_DSN: str = os.getenv("SENTRY_DSN", "")

    # -----------------------------
    # App-level secret
    # -----------------------------
    APP_SECRET_KEY: str = os.getenv("APP_SECRET_KEY", "insecure_dev_key")

    # -----------------------------
    # Audio processing
    # -----------------------------
    AUDIO_TEMP_DIR: str = os.getenv("AUDIO_TEMP_DIR", "/tmp/presentos_audio")
    FFMPEG_BINARY: str = os.getenv("FFMPEG_BINARY", "ffmpeg")


# Singleton instance
settings = Settings()
