
"""
Telegram Bot - Polling Mode (Localhost Friendly)

Run this script to:
1. Listen for messages.
2. Get your Chat ID (printed to console).
3. Interact with PresentOS via Telegram.

Usage: python scripts/run_telegram_bot.py
"""

import sys
import os
import time
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.integrations.telegram_client import TelegramClient

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger("TelegramBot")

def run_bot():
    client = TelegramClient.create_from_env()
    if not client:
        logger.error("TELEGRAM_BOT_TOKEN missing in .env")
        return

    me = client.get_me()
    if not me.get("ok"):
        logger.error(f"Auth failed: {me}")
        return
    
    bot_name = me['result']['username']
    logger.info(f"Bot started: @{bot_name}")
    logger.info("Waiting for messages... (Send a message to your bot to get Chat ID)")

    offset = None
    
    while True:
        try:
            updates = client.get_updates(offset=offset, timeout=30)
            
            for update in updates:
                offset = update["update_id"] + 1
                
                if "message" in update:
                    msg = update["message"]
                    chat_id = msg["chat"]["id"]
                    text = msg.get("text", "")
                    user = msg.get("from", {}).get("username", "Unknown")
                    
                    logger.info(f"📩 Message from @{user} (ID: {chat_id}): {text}")
                    print(f"\n✅ YOUR CHAT ID IS: {chat_id}\n")
                    
                    # Handle /start command
                    if text == "/start":
                        reply = f"👋 Hello! Connected to PresentOS.\nYour Chat ID is: `{chat_id}`\n\nI'm Martin, your AI assistant. Try:\n• What's on my schedule?\n• Add task review code\n• Start focus session\n• Check emails"
                        client.send_message(reply, chat_id=str(chat_id))
                    else:
                        # Call Present OS API
                        try:
                            import requests
                            base_url = os.getenv("APP_BASE_URL", "http://localhost:8080")
                            api_url = f"{base_url}/api/chat"
                            
                            payload = {
                                "message": text,
                                "user_id": f"telegram_{chat_id}",
                                "channel": "telegram"
                            }
                            
                            logger.info(f"🔄 Calling Present OS API: {text}")
                            response = requests.post(api_url, json=payload, timeout=30)
                            
                            if response.status_code == 200:
                                data = response.json()
                                reply = data.get("response", "Done!")
                                logger.info(f"✅ API Response: {reply[:100]}...")
                            else:
                                reply = f"⚠️ API Error ({response.status_code}). Backend might be down."
                                logger.error(f"API returned {response.status_code}: {response.text[:200]}")
                        
                        except requests.exceptions.ConnectionError:
                            reply = "⚠️ Cannot connect to Present OS backend. Make sure it's running:\n`uvicorn app.api:app --host 0.0.0.0 --port 8080`"
                            logger.error("Connection refused - backend not running")
                        except Exception as e:
                            reply = f"⚠️ Error: {str(e)[:100]}"
                            logger.error(f"API call failed: {e}")
                        
                        client.send_message(reply, chat_id=str(chat_id))
                    
            time.sleep(1)
            
        except KeyboardInterrupt:
            logger.info("Bot stopped by user")
            break
        except Exception as e:
            logger.error(f"Polling error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_bot()
