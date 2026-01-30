"""
Quick Agent Verification Script
Run this before recording to verify all agents are working.
Usage: python scripts/quick_verify_agents.py
"""

import requests
import sys

BASE_URL = "http://localhost:8080"

# One test per agent
QUICK_TESTS = [
    ("Task Agent", "Add task test verification"),
    ("Calendar Agent", "What's on my schedule today?"),
    ("Weather Agent", "Weather in Pune"),
    ("XP Agent", "Show my XP status"),
    ("Email Agent", "Check my emails"),
    ("Focus Agent", "Start a focus session"),
    ("Finance Agent", "Show my budget"),
    ("Contact Agent", "Show my contacts"),
    ("Research Agent", "Research AI productivity"),
    ("Plan Report", "What's my plan for today?"),
]

def main():
    print("=" * 50)
    print("PRESENT OS - QUICK AGENT VERIFICATION")
    print("=" * 50)
    
    # Check server
    try:
        requests.get(f"{BASE_URL}/api/status", timeout=5)
        print("[OK] Server is running\n")
    except:
        print("[ERROR] Server not running!")
        print("Start with: uvicorn app.api:app --host 0.0.0.0 --port 8080")
        sys.exit(1)
    
    passed = 0
    for agent, query in QUICK_TESTS:
        try:
            r = requests.post(f"{BASE_URL}/api/chat", json={"message": query}, timeout=60)
            if r.status_code == 200 and r.json().get("response"):
                print(f"[PASS] {agent}")
                passed += 1
            else:
                print(f"[FAIL] {agent}")
        except Exception as e:
            print(f"[ERROR] {agent}: {str(e)[:40]}")
    
    # Test Voice TTS
    try:
        r = requests.post(f"{BASE_URL}/api/voice/tts", 
                         json={"message": "Test"}, timeout=30)
        if r.status_code == 200 and len(r.content) > 100:
            print(f"[PASS] Voice TTS (Murf)")
            passed += 1
        else:
            print(f"[FAIL] Voice TTS")
    except:
        print(f"[ERROR] Voice TTS")
    
    # Test Telegram Bot (check if configured)
    import os
    telegram_token = os.getenv("TELEGRAM_BOT_TOKEN")
    telegram_chat = os.getenv("TELEGRAM_CHAT_ID")
    if telegram_token and telegram_chat:
        print(f"[PASS] Telegram Bot (configured)")
        print(f"       Run: python scripts/run_telegram_bot.py")
        passed += 1
    else:
        print(f"[SKIP] Telegram Bot (not configured in .env)")
    
    total_tests = len(QUICK_TESTS) + 2  # +1 Voice, +1 Telegram
    print("\n" + "=" * 50)
    print(f"RESULT: {passed}/{total_tests} agents verified")
    
    if passed == len(QUICK_TESTS) + 1:
        print("ALL SYSTEMS GO! Ready for video recording.")
    else:
        print("Some agents have issues. Check logs.")
    print("=" * 50)

if __name__ == "__main__":
    main()
