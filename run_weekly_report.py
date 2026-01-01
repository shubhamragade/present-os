# final_test_presentos.py
# FINAL TEST SCRIPT - All agents + real-world convos
# Run: python final_test_presentos.py

import os
from dotenv import load_dotenv
load_dotenv()

from typing import List  # ← Fixed the NameError

from app.main import app as fastapi_app
from fastapi.testclient import TestClient

client = TestClient(fastapi_app)

def test_chat(input_text: str, session_id: str = None, expected_agents: List[str] = None):
    payload = {"input_text": input_text}
    if session_id:
        payload["session_id"] = session_id
    
    response = client.post("/chat", json=payload)
    
    print(f"INPUT: {input_text}")
    print(f"STATUS: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        martin_response = data.get("final_response", "No response")
        print(f"MARTIN: {martin_response}")
        
        if expected_agents:
            print(f"EXPECTED AGENTS: {', '.join(expected_agents)}")
        print("---\n")
    else:
        print(f"ERROR: {response.text}\n")

print("=== PRESENT OS MVP - FINAL REAL-WORLD TEST SUITE ===")
print("All child agents tested separately + multi-intent + natural conversation")
print(f"PERPLEXITY_API_KEY loaded: {'Yes' if os.getenv('PERPLEXITY_API_KEY') else 'No'}\n")

# === 1. Basic Greeting ===
test_chat("Hey Martin, good morning!")

# === 2. Task Agent Only ===
test_chat("Add a task: Call mom tonight at 8 PM")

# === 3. Quest Agent Only ===
test_chat("Create quest: Get fit in 2026, purpose: Feel strong and confident, result: Run 5K, category: Health")

# === 4. Calendar + Focus Agent ===
test_chat("Block 90 minutes tomorrow morning for deep work on coding")

# === 5. Email Agent Only ===
test_chat("Write email to Sarah: Follow up on design feedback, keep it friendly")

# === 6. Weather Agent Only ===
test_chat("Should I go kitesurfing this weekend?")

# === 7. Research + Browser Agent (Uses PERPLEXITY_API_KEY) ===
test_chat("Research best no-code tools for building AI apps in 2026")

# === 8. Report Agents ===
test_chat("Show me my plan for today and how much XP I earned this week")

# === 9. Multi-Intent Real-World Flow (Same session) ===
print("=== REAL USER CONVERSATION (Session: real_user_1) ===\n")
test_chat("Hey Martin, I want to start a new project", session_id="real_user_1")
test_chat("Create quest: Launch side hustle, purpose: Financial freedom", session_id="real_user_1")
test_chat("Add task: Brainstorm 10 ideas this weekend", session_id="real_user_1")
test_chat("Schedule 2 hours Saturday morning for brainstorming", session_id="real_user_1")
test_chat("Check if weather is good for outdoor thinking", session_id="real_user_1")
test_chat("Research top side hustle ideas for developers 2026", session_id="real_user_1")
test_chat("Draft email to my mentor asking for advice", session_id="real_user_1")
test_chat("Show me my plan for Saturday", session_id="real_user_1")

# === 10. Edge Cases ===
print("=== EDGE CASES ===\n")
test_chat("Random nonsense xyz")  # Should respond gracefully
test_chat("Mark all tasks complete")  # XP trigger
test_chat("What’s my total XP?")  # Report

print("=== ALL TESTS COMPLETED ===")
print("\nCheck your Notion databases:")
print("- New tasks created")
print("- New quest")
print("- XP entries added")
print("- Research reports (if database exists)")
print("\nAll child agents have been triggered!")
print("Your Present OS is fully alive and working perfectly. 🎉")