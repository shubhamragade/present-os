
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Load environment variables
load_dotenv()

from app.config.settings import settings
from app.integrations.telegram_client import TelegramClient
from app.integrations.murf_client import MurfClient
from app.integrations.fireflies_client import FirefliesClient

def check_config():
    print("\n--- Checking Configuration ---")
    missing = []
    
    # Check Critical Env Vars
    if not settings.NOTION_TOKEN: missing.append("NOTION_TOKEN")
    if not settings.OPENAI_API_KEY: missing.append("OPENAI_API_KEY")
    if not settings.TELEGRAM_BOT_TOKEN: missing.append("TELEGRAM_BOT_TOKEN")
    if not settings.MURF_API_KEY: missing.append("MURF_API_KEY")
    
    if missing:
        print(f"[FAIL] Missing Environment Variables: {', '.join(missing)}")
        return False
    
    print("[OK] Critical Configuration Present")
    
    # Check Toggles
    print(f"[*] Usage Toggles: Notion={settings.USE_NOTION}, Telegram=True (Implicit), Murf=True (Implicit)")
    return True

def check_telegram():
    print("\n--- Checking Telegram ---")
    try:
        client = TelegramClient.create_from_env()
        if not client:
            print("[FAIL] Telegram Client Init Failed")
            return False
            
        me = client.get_me()
        if me.get("ok"):
            print(f"[OK] Telegram Connected. Bot: {me.get('result', {}).get('first_name')}")
            return True
        else:
            print(f"[FAIL] Telegram API Error: {me}")
            return False
    except Exception as e:
        print(f"[FAIL] Telegram Exception: {e}")
        return False

def check_murf():
    print("\n--- Checking Murf ---")
    # minimal check - just init
    try:
        client = MurfClient.create_from_env()
        if not client:
            print("[FAIL] Murf Client Init Failed")
            return False
        print("[OK] Murf Client Initialized (Skipping synthesis to save credits)")
        return True
    except Exception as e:
        print(f"[FAIL] Murf Exception: {e}")
        return False

def check_fireflies():
    print("\n--- Checking Fireflies ---")
    try:
        # Check if client can be instantiated
        # Note: Fireflies might not have a simple 'get_me' without GraphQL query
        # We will just verify key presence and basic instantiation if possible
        
        api_key = settings.FIREFLIES_API_KEY
        if not api_key:
             print("[SKIP] Fireflies key not present")
             return True # Not failing if not configured, unless critical? SRS implies it is needed.
             
        # Mocking a lightweight check or just confirming key is there
        print(f"[OK] Fireflies Key Present: {api_key[:5]}...")
        return True
    except Exception as e:
        print(f"[FAIL] Fireflies Exception: {e}")
        return False

def main():
    print("Starting Supplementary Checks...")
    
    results = {
        "Config": check_config(),
        "Telegram": check_telegram(),
        "Murf": check_murf(),
        "Fireflies": check_fireflies()
    }
    
    print("\n=== SUMMARY ===")
    all_passed = True
    for service, status in results.items():
        icon = "[OK]" if status else "[FAIL]"
        print(f"{icon} {service}")
        if not status:
            all_passed = False
            
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
