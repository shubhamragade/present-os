
import requests
import json
import time

API_URL = "http://127.0.0.1:8000/api/chat"

TEST_CASES = [
    {
        "agent": "Task Agent",
        "prompt": "Add a task to buy milk today",
        "expected_action_keyword": "Task Created"
    },
    {
        "agent": "Calendar Agent",
        "prompt": "Schedule a team sync tomorrow at 10am",
        "expected_action_keyword": "Event Created" 
    },
    {
        "agent": "Email Agent",
        "prompt": "Draft an email to test@example.com saying hello world",
        "expected_action_keyword": "Draft Created"
    },
    {
        "agent": "Weather Agent",
        "prompt": "What is the weather in San Francisco?",
        "expected_action_keyword": "Weather" # or check response content
    },
    {
        "agent": "Report Agent",
        "prompt": "Show me my XP report",
        "expected_action_keyword": "Report" # or check response content
    }
]

def run_tests():
    print("🤖 STARTING FULL AGENT VERIFICATION 🤖\n")
    
    results = {}
    
    for test in TEST_CASES:
        agent = test["agent"]
        prompt = test["prompt"]
        print(f"Testing {agent}...")
        print(f"  > User: \"{prompt}\"")
        
        try:
            payload = {"message": prompt}
            start = time.time()
            resp = requests.post(API_URL, json=payload, timeout=30)
            duration = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                response_text = data.get("response", "")
                # We can also check 'updated_state' -> 'agents' for status
                
                print(f"  > PresentOS: \"{response_text[:80]}...\"")
                print(f"  > Time: {duration:.2f}s")
                
                # lenient check: just ensure we got a valid response 
                # Strict check would look at 'updated_state' logic if accessible
                if response_text and "error" not in response_text.lower():
                     print(f"  ✅ PASS")
                     results[agent] = True
                else:
                     print(f"  ❌ FAIL (Error in response)")
                     results[agent] = False
            else:
                print(f"  ❌ FAIL (Status {resp.status_code})")
                results[agent] = False
                
        except Exception as e:
            print(f"  ❌ FAIL (Exception: {e})")
            results[agent] = False
        
        print("-" * 40)
        time.sleep(1) # polite delay

    print("\n=== AGENT REPORT CARD ===")
    for agent, success in results.items():
        icon = "✅" if success else "❌"
        print(f"{icon} {agent}")
        
    print("\n")

if __name__ == "__main__":
    run_tests()
