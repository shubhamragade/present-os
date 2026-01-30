
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.graph.state import PresentOSState
from app.graph.nodes.browser_agent import run_browser_node

# Setup Logging
logging.basicConfig(level=logging.INFO)

def test_browse():
    print("\n>>> TESTING BROWSE AGENT <<<")
    state = PresentOSState()
    
    # Simulate Parent Instruction
    state.parent_decision = {
        "instructions": [{
            "agent": "browser_agent",
            "intent": "read_research",
            "query": "What are the top 3 agentic AI frameworks in 2025?",
            "schedule_weekly": False
        }]
    }
    
    # Run Agent
    new_state = run_browser_node(state)
    
    outputs = [out for out in new_state.agent_outputs if out.agent_name == "browser_agent"]
    for out in outputs:
        print(f"Full Result: {out.result}")
        if out.result.get("status") == "error":
            print(f"❌ AGENT ERROR: {out.result.get('error')}")
        else:
             res_data = out.result.get('result', {})
             print(f"Result: {res_data.get('answer', '')[:100]}...")
             if out.result.get("full_result"):
                  print(f"Sources: {len(out.result['full_result'].get('sources', []))}")

if __name__ == "__main__":
    test_browse()
