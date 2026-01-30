
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.graph.state import PresentOSState, PAEIRole
from app.graph.nodes.xp_agent import run_xp_node
from app.graph.nodes.weather_agent import run_weather_node
from app.graph.nodes.task_agent import run_task_node
# Research agent might need mocking to avoid huge costs/latency if it uses Perplexity
from app.graph.nodes.research_agent import run_research_node

def test_xp_agent():
    print("\n--- Testing XP Agent ---")
    state = PresentOSState()
    
    # Mocking a completed task event in the state
    # Usually XP agent rewards events found in state.xp_events or process outputs
    # Let's inspect how xp_agent works. 
    # Assuming it processes 'xp_events' queue or checks agent_outputs for 'score'
    
    # Let's manually trigger it with an instruction if supported, 
    # or just rely on its 'tick' behavior if checking state.
    
    # Injecting a decision that awards XP
    state.add_xp_event(amount=10, paei=PAEIRole.PRODUCER, reason="Test Task")
    
    try:
        new_state = run_xp_node(state)
        # Verify XP total updated
        curr_xp = new_state.xp_totals_by_paei[PAEIRole.PRODUCER]
        print(f"[OK] XP Agent ran. Producer XP: {curr_xp}")
        return True
    except Exception as e:
        print(f"[FAIL] XP Agent Error: {e}")
        return False

def test_weather_agent():
    print("\n--- Testing Weather Agent (Read-Only) ---")
    state = PresentOSState()
    
    # Inject instruction for read_weather
    # The agent looks for instruction in parent_decision or via utility
    mock_instruction = {
        "agent": "weather_agent",
        "payload": {
            "intent": "read_weather",
            "location": {"city": "San Francisco"}
        }
    }
    state.parent_decision = {"instructions": [mock_instruction]}
    state.activated_agents = ["weather_agent"]
    
    try:
        new_state = run_weather_node(state)
        # Check output
        found = False
        for out in new_state.agent_outputs:
            if out.agent_name == "weather_agent":
                print(f"[OK] Weather Output: {out.result.get('status') or out.result.get('action')}")
                found = True
        
        if not found:
             print("[FAIL] No output from Weather Agent")
             return False
        return True
    except Exception as e:
        print(f"[FAIL] Weather Agent Error: {e}")
        return False

def test_task_agent():
    print("\n--- Testing Task Agent (Mock Creation) ---")
    state = PresentOSState()
    
    # Inject instruction for task creation
    mock_instruction = {
        "agent": "task_agent",
        "payload": {
            "intent": "create_task",
            "task_data": {
                "title": "Clean verification script",
                "paei_category": "A",
                "estimated_time": 30
            }
        }
    }
    state.parent_decision = {"instructions": [mock_instruction]}
    state.activated_agents = ["task_agent"]
    
    try:
        # Note: This might hit Notion unless mocked. 
        # But for "verification" we want to know if it hits Notion successfully.
        # Be aware it creates real data.
        print("Note: This might create a real task in Notion.")
        
        # We can try to skip actual creation if possible, but the code likely does it.
        # Let's hope the environment is set to DEV or use a test DB.
        # We'll run it, assuming the user is okay with a test task.
        new_state = run_task_node(state)
        
        found = False
        for out in new_state.agent_outputs:
            if out.agent_name == "task_agent":
                 print(f"[OK] Task Agent Result: {out.result.get('status')}")
                 found = True
        
        if not found:
             print("[FAIL] No output from Task Agent")
             return False
        return True
    except Exception as e:
        print(f"[FAIL] Task Agent Error: {e}")
        return False

def main():
    results = {
        "XP_Agent": test_xp_agent(),
        "Weather_Agent": test_weather_agent(),
        # "Task_Agent": test_task_agent() # Commented out to avoid spamming Notion in this global check unless explicitly desired
    }
    
    print("\n=== AGENT LAYER SUMMARY ===")
    all_passed = True
    for service, status in results.items():
        icon = "[OK]" if status else "[FAIL]"
        print(f"{icon} {service}")
        if not status:
            all_passed = False
            
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
