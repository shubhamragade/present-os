"""
Quick test script to verify Weather Agent functionality
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_weather_agent():
    """Test weather agent with a simple query"""
    
    print("=" * 60)
    print("TESTING WEATHER AGENT")
    print("=" * 60)
    
    test_queries = [
        "What's the weather like today?",
        "Should I go kitesurfing?",
        "Is it good weather for outdoor work?",
        "Check weather in Pune"
    ]
    
    for query in test_queries:
        print(f"\n📝 Query: {query}")
        print("-" * 60)
        
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
                print(data.get('response', '')[:500])
                
                # Check if weather agent was activated
                if 'updated_state' in data:
                    agents = data['updated_state'].get('activated_agents', [])
                    if 'weather_agent' in agents:
                        print(f"\n✅ Weather Agent ACTIVATED")
                    else:
                        print(f"\n⚠️ Weather Agent NOT in activated agents: {agents}")
                
            else:
                print(f"❌ Status: {response.status_code}")
                print(f"Error: {response.text[:200]}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️ TIMEOUT - Request took > 30 seconds")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()

if __name__ == "__main__":
    test_weather_agent()
