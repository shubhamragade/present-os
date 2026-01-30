import requests
import json
import os

BASE_URL = "http://localhost:8080"
LOG_FILE = "c:/present-os/tests/contact_test_results.txt"

def log(msg):
    print(msg)
    with open(LOG_FILE, "a") as f:
        f.write(msg + "\n")

if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

log("Testing Contact Agent Integration...")

# 1. Add note
log("\n1. Testing: Adding a note")
query = "Sarah prefers phone calls over email."
log(f"Query: {query}")
try:
    resp = requests.post(f"{BASE_URL}/api/chat", json={"message": query}, timeout=60)
    log(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        log(f"Response: {resp.json().get('response')}")
    else:
        log(f"Error: {resp.text}")
except Exception as e:
    log(f"Failed: {e}")

# 2. Lookup
log("\n2. Testing: Lookup")
query = "what do I know about Sarah?"
log(f"Query: {query}")
try:
    resp = requests.post(f"{BASE_URL}/api/chat", json={"message": query}, timeout=60)
    log(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        log(f"Response: {resp.json().get('response')}")
    else:
        log(f"Error: {resp.text}")
except Exception as e:
    log(f"Failed: {e}")
