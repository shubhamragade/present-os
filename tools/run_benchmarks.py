import requests
import json
import time
import sys

# Ensure UTF-8 output even on Windows
if sys.platform == "win32":
    import codecs
    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach())

API_URL = "http://127.0.0.1:8080/api/chat"

# Removed emojis for Windows compatibility
EXAMPLES = [
    {
        "name": "Example 1: Complex Orchestration",
        "prompt": "Tomorrow morning I have good energy, schedule deep work 9-12, move my 10am call if possible, and check if my camera is still on sale on Amazon."
    },
    {
        "name": "Example 4: Task + RPM",
        "prompt": "Add task: Review investment portfolio this Sunday."
    },
    {
        "name": "Example 5: Research",
        "prompt": "Quick research: what are people saying about Grok 4 on X right now?"
    },
    {
        "name": "Example 2: Email + Task",
        "prompt": "Reply to the invoice from electricity company - tell them I will pay next week and ask for extended due date."
    }
]

def run_benchmarks():
    print("STARTING SYSTEM BENCHMARK\n")
    
    for ex in EXAMPLES:
        print(f"=== {ex['name']} ===")
        print(f"User: \"{ex['prompt']}\"")
        
        try:
            start = time.time()
            resp = requests.post(API_URL, json={"message": ex["prompt"]}, timeout=120)
            duration = time.time() - start
            
            if resp.status_code == 200:
                data = resp.json()
                print(f"Martin: \"{data.get('response')}\"")
                print(f"XP Awarded: {data.get('xp_awarded')} ({data.get('paei')})")
                print(f"Time Taken: {duration:.2f}s")
                
                tasks = data.get("updated_state", {}).get("tasks", [])
                if tasks:
                    print(f"Tasks Updated: {len(tasks)} items")
            else:
                print(f"Error: Status {resp.status_code} - {resp.text}")
                
        except Exception as e:
            print(f"Exception: {e}")
        
        print("-" * 40)
        time.sleep(2)

if __name__ == "__main__":
    run_benchmarks()
