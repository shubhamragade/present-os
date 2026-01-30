
import requests
import json
import time

API_URL = "http://localhost:8000/api/chat"

def test_contact_retrieval():
    print(f"Testing Contact Retrieval on {API_URL}...")
    
    payload = {
        "message": "Show contact details for Sarah",
        "voice_mode": False
    }
    
    start_time = time.time()
    try:
        response = requests.post(API_URL, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        print("\n--- Response ---")
        print(json.dumps(data, indent=2))
        
        elapsed = time.time() - start_time
        print(f"\nTime taken: {elapsed:.2f}s")
        
        response_text = data.get("response", "")
        print(f"Response: {response_text}")

        if "itachiuchiha8june@gmail.com" in response_text:
             print("\n[SUCCESS]: Real email address found!")
        elif "example.com" in response_text:
             print("\n[FAILURE]: Hallucinated placeholder email found.")
        elif "Sarah" in response_text:
             print("\n[PARTIAL]: 'Sarah' found but email might be missing.")
        else:
             print("\n[FAILURE]: Sarah not found.")
             
    except Exception as e:
        print(f"\n[ERROR]: API request failed: {e}")

if __name__ == "__main__":
    test_contact_retrieval()
