
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.integrations.telegram_client import TelegramClient

logging.basicConfig(level=logging.INFO)

def test_telegram():
    print("\n>>> TESTING TELEGRAM CLIENT <<<")
    
    client = TelegramClient.create_from_env()
    if not client:
        print("❌ SKIPPING: TELEGRAM_BOT_TOKEN missing")
        return

    # 1. Check Auth
    print("1. Checking Bot Identity (getMe)...")
    me = client.get_me()
    if me.get("ok"):
        print(f"✅ Bot connected: @{me['result']['username']} (ID: {me['result']['id']})")
    else:
        print(f"❌ Auth Failed: {me}")
        return

    # 2. Try Send Message
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not chat_id:
        print("⚠️  TELEGRAM_CHAT_ID missing in .env - Cannot test sending messages.")
        print("   (You can find your ID by messaging @userinfobot)")
    else:
        print(f"2. Sending test message to {chat_id}...")
        res = client.send_message("🔔 Test message from *PresentOS*", chat_id=chat_id)
        if res.get("ok"):
            print("✅ Message sent successfully!")
        else:
            print(f"❌ Send Failed: {res}")

if __name__ == "__main__":
    test_telegram()
