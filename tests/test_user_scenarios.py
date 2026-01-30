"""
Test User Provided Scenarios
"""
import requests
import json
import time

BASE_URL = "http://localhost:8080"
GREEN = "\033[92m"
CYAN = "\033[96m"
RED = "\033[91m"
RESET = "\033[0m"

SCENARIOS = [
    "Good morning, what's on my schedule today?",
    "Add task review project proposal due Friday",
    "Create task call client about feedback",
    "Show my tasks",
    "Block deep work tomorrow morning 9 to 12",
    "Schedule team sync Friday at 3 PM",
    "What’s the weather like today in Pune?",
    "Is it good weather for outdoor work in Pune today?",
    "Check my emails",
    "Research best practices for API design 2026",
    "Schedule deep work tomorrow, check my emails, and research latest AI trends in productivity",
    "Tell me today's plan and add task call mom tonight",
    "Show my XP status",
    "Start 90 minute focus session now",
    "Reply to the latest email saying thank you",
    "Check weather in Pune",
    "Block time for concentration tomorrow afternoon",
    "Research latest AI trends in no-code tools",
    "Free up weekend for family",
    "What's my plan report for today?",
    "Add task finish quarterly review by end of week"
]

def test_scenarios():
    print(f"{CYAN}🚀 Testing User Scenarios...{RESET}\n")
    
    results = []
    
    for query in SCENARIOS:
        print(f"🔹 Query: '{query}'")
        try:
            start = time.time()
            resp = requests.post(
                f"{BASE_URL}/api/chat",
                json={"message": query},
                timeout=45
            )
            duration = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                response_text = data.get("response", "")
                
                # Try to extract what actually happened from the response text or logs
                # Since we don't have the internal state here, we rely on the text response
                print(f"{GREEN}   ✅ Response ({duration:.1f}s):{RESET} {response_text.strip()[:150]}...")
                results.append({"query": query, "status": "PASS", "response": response_text})
            else:
                print(f"{RED}   ❌ Failed (Status {resp.status_code}):{RESET} {resp.text}")
                results.append({"query": query, "status": "FAIL", "error": resp.text})
                
        except Exception as e:
            print(f"{RED}   ❌ Error:{RESET} {e}")
            results.append({"query": query, "status": "ERROR", "error": str(e)})
        
        print("-" * 50)
        time.sleep(1) # Slight pause between requests

    print(f"\n{CYAN}📊 Summary:{RESET}")
    passed = sum(1 for r in results if r["status"] == "PASS")
    print(f"Passed: {passed}/{len(results)}")

if __name__ == "__main__":
    test_scenarios()
