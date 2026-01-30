"""
Test Focus Agent Enhanced Features
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_focus_agent():
    """Test enhanced focus agent with detailed responses"""
    
    print("=" * 70)
    print("TESTING ENHANCED FOCUS AGENT")
    print("=" * 70)
    
    test_queries = [
        "Start 90 minute focus session",
        "Block time for concentration",
        "Deep work now",
        "Enable focus mode for 2 hours"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 70)
        
        try:
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={"message": query},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Status: {response.status_code}")
                print(f"🤖 PAEI: {data.get('paei')}")
                print(f"⭐ XP: {data.get('xp_awarded', 0)}")
                print(f"\n💬 Response:")
                print(data.get('response', ''))
                
                # Check for expected details in response
                response_text = data.get('response', '').lower()
                
                checks = {
                    "Has exact time": any(x in response_text for x in ['pm', 'am', ':']),
                    "Has WHOOP context": 'recovery' in response_text or 'energy' in response_text,
                    "Has protections": 'calendar' in response_text or 'notifications' in response_text or 'blocked' in response_text,
                    "Has XP award": 'xp' in response_text or 'producer' in response_text
                }
                
                print(f"\n✓ Response Quality Checks:")
                for check, passed in checks.items():
                    status = "✅" if passed else "⚠️"
                    print(f"  {status} {check}: {passed}")
                
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️ TIMEOUT - Request took > 30 seconds")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_focus_agent()
