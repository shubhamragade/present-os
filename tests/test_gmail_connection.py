"""
Test Gmail API Connection
"""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

print("=" * 70)
print("TESTING GMAIL API CONNECTION")
print("=" * 70)

# Check credentials
print("\n1. Checking .env credentials...")
gmail_token = os.getenv("GMAIL_REFRESH_TOKEN")
client_id = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
client_secret = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")

if gmail_token:
    print(f"✅ GMAIL_REFRESH_TOKEN: {gmail_token[:20]}...")
else:
    print("❌ GMAIL_REFRESH_TOKEN: Missing")

if client_id:
    print(f"✅ GOOGLE_OAUTH_CLIENT_ID: {client_id[:30]}...")
else:
    print("❌ GOOGLE_OAUTH_CLIENT_ID: Missing")

if client_secret:
    print(f"✅ GOOGLE_OAUTH_CLIENT_SECRET: {client_secret[:20]}...")
else:
    print("❌ GOOGLE_OAUTH_CLIENT_SECRET: Missing")

# Test Gmail connection
print("\n2. Testing Gmail API connection...")
try:
    from app.integrations.gmail_client import fetch_unread_messages
    
    print("Fetching unread emails...")
    emails = fetch_unread_messages(max_results=5)
    
    print(f"\n✅ SUCCESS! Fetched {len(emails)} unread emails")
    
    if emails:
        print("\nEmails found:")
        for i, email in enumerate(emails, 1):
            subject = email.get("subject", "No subject")
            sender = email.get("from", "Unknown")
            print(f"  {i}. {subject}")
            print(f"     From: {sender}")
    else:
        print("\n📭 No unread emails in inbox")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
