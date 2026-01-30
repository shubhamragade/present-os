
import os
from dotenv import load_dotenv
from app.integrations.elevenlabs_client import ElevenLabsClient

load_dotenv()

def test_elevenlabs_auth():
    print("Testing ElevenLabs Auth...")
    client = ElevenLabsClient.create_from_env()
    
    if not client:
        print("❌ Client creation failed (Missing ENV var)")
        return
        
    print(f"Using API Key: {client.api_key[:5]}...{client.api_key[-3:]}")
    
    # Simple GET request to check auth
    print("Attempting to list voices...")
    result = client.list_voices()
    
    if "error" in result:
        print(f"❌ API Error: {result['error']}")
    else:
        print("[OK] Auth Successful! Voices retrieved.")
        print(f"Voices found: {len(result.get('voices', []))}")

if __name__ == "__main__":
    test_elevenlabs_auth()
