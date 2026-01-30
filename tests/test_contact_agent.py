"""
Test Contact Agent Functionality
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_contact_note():
    """Test adding a note to a contact"""
    print("\n1. Testing: Adding a note to a contact")
    query = "Sarah prefers phone calls over email."
    print(f"Query: {query}")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": query}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Response: {data.get('response')}")
            print(f"PAEI: {data.get('paei')}")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")

def test_contact_lookup():
    """Test looking up a contact"""
    print("\n2. Testing: Looking up contact info")
    query = "what do I know about Sarah?"
    print(f"Query: {query}")
    
    try:
        resp = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": query}
        )
        print(f"Status: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"Response: {data.get('response')}")
        else:
            print(f"Error: {resp.text}")
    except Exception as e:
        print(f"Request failed: {e}")

if __name__ == "__main__":
    # Ensure backend is running
    print("Testing Contact Agent Integration...")
    test_contact_note()
    test_contact_lookup()
