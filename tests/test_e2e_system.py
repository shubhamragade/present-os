"""
Present OS - Comprehensive System E2E Test
Tests the core API and all major agents via the chat interface.
"""

import requests
import json
import time
import sys

BASE_URL = "http://localhost:8080"
GREEN = "\033[92m"
RED = "\033[91m"
CYAN = "\033[96m"
RESET = "\033[0m"

def log(msg, color=RESET):
    print(f"{color}{msg}{RESET}")

def check_endpoint(name, method, endpoint, payload=None):
    url = f"{BASE_URL}{endpoint}"
    start = time.time()
    try:
        if method == "GET":
            resp = requests.get(url, timeout=10)
        else:
            resp = requests.post(url, json=payload, timeout=60)
            
        duration = time.time() - start
        
        if resp.status_code == 200:
            log(f"✅ {name}: PASS ({duration:.2f}s)", GREEN)
            return resp.json()
        else:
            log(f"❌ {name}: FAILED (Status {resp.status_code})", RED)
            log(f"   Response: {resp.text}", RED)
            return None
    except Exception as e:
        log(f"❌ {name}: ERROR ({e})", RED)
        return None

def test_system():
    log("\n🚀 STARTING PRESENT OS SYSTEM CHECK...\n", CYAN)
    
    # 1. API Health
    status = check_endpoint("API Health", "GET", "/api/status")
    if status:
        log(f"   Greeting: {status.get('greeting')}")
        log(f"   XP: {status.get('updated_state', {}).get('xp_data', {}).get('total')}")

    # 2. Energy Data
    energy = check_endpoint("WHOOP Energy", "GET", "/api/energy")
    if energy:
        log(f"   Score: {energy.get('recovery_score')}")

    # 3. Chat - Greeting (Basic LLM)
    chat_basic = check_endpoint("Agent: Chat (Basic)", "POST", "/api/chat", {"message": "Hello Martin"})
    if chat_basic:
        log(f"   Response: {chat_basic.get('response')[:100]}...")

    # 4. Chat - Contact Memory (Notion + recent fix)
    chat_contact = check_endpoint("Agent: Contact (Memory)", "POST", "/api/chat", {"message": "What do I know about Sarah?"})
    if chat_contact:
        log(f"   Response: {chat_contact.get('response')}")

    # 5. Chat - Weather (Tool use)
    chat_weather = check_endpoint("Agent: Weather", "POST", "/api/chat", {"message": "Check the weather"})
    if chat_weather:
        log(f"   Response: {chat_weather.get('response')[:100]}...")

    # 6. Notifications
    notifs = check_endpoint("Notifications", "GET", "/api/notifications")
    if notifs is not None:
        log(f"   Count: {len(notifs)}")

    log("\n✨ SYSTEM CHECK COMPLETE ✨", CYAN)

if __name__ == "__main__":
    test_system()
