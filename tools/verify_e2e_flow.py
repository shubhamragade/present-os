
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.graph.state import PresentOSState
from app.graph.graph_executor import build_presentos_graph

def test_e2e_weather():
    print("\n--- Testing E2E Flow: Weather Check ---")
    
    graph = build_presentos_graph()
    
    # Simple read-only query
    state = PresentOSState(
        input_text="What is the weather in San Francisco today?",
        user_id="verification_user"
    )
    
    try:
        final_state = graph.invoke(state)
        
        print(f"[INFO] Final Response: {final_state.final_response}")
        
        # Verify agents activated
        activated = final_state.activated_agents
        print(f"[INFO] Activated Agents: {activated}")
        
        if "weather_agent" in activated:
            print("[OK] Weather Agent was activated.")
        else:
            print("[FAIL] Weather Agent was NOT activated.")
            return False
            
        if final_state.final_response and len(final_state.final_response) > 10:
             print("[OK] Valid Final Response generated.")
             return True
        else:
             print("[FAIL] Final Response missing or too short.")
             return False
             
    except Exception as e:
        print(f"[FAIL] E2E Execution Error: {e}")
        return False

def main():
    if test_e2e_weather():
        print("\n[OK] E2E Verification Passed")
        sys.exit(0)
    else:
        print("\n[FAIL] E2E Verification Failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
