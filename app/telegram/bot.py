# app/telegram/bot.py
from __future__ import annotations

import os
import logging
import httpx

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

logger = logging.getLogger("presentos.telegram")

API_URL = os.getenv("PRESENTOS_API_URL", "http://localhost:8000/chat")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN missing")


# -------------------------------------------------
# Message Handler
# -------------------------------------------------
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = update.message.text

    payload = {
        "session_id": f"telegram:{user.id}",
        "user_id": str(user.id),
        "input_channel": "telegram_text",
        "input_text": text,   # ✅ FIXED
    }

    try:
        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        await update.message.reply_text(
            data.get("final_response", "Done.")
        )

    except Exception:
        logger.exception("Telegram request failed")
        await update.message.reply_text(
            "Something went wrong. Please try again."
        )


# -------------------------------------------------
# Bootstrap
# -------------------------------------------------
def run_telegram_bot():
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text)
    )

    logger.info("Telegram bot started")
    app.run_polling()
