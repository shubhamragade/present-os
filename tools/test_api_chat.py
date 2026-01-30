
import requests
import json
import sys

def test_chat_api():
    url = "http://127.0.0.1:8000/api/chat"
    payload = {"message": "What is my plan today?"}
    headers = {"Content-Type": "application/json"}
    
    print(f"\nTesting API: {url}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\n✅ API Success!")
            print(f"Response: {data.get('response')}")
            print(f"Agent Action: {data.get('updated_state', {}).get('agents', [])}")
        else:
            print(f"\n❌ API Failed: {response.text}")
            
    except Exception as e:
        print(f"\n❌ Connection Error: {e}")

if __name__ == "__main__":
    test_chat_api()
