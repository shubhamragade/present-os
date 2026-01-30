
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.graph.state import PresentOSState
from app.graph.nodes.finance_agent import run_finance_node

logging.basicConfig(level=logging.INFO)

def test_finance():
    print("\n>>> TESTING FINANCE AGENT <<<")
    state = PresentOSState()
    
    # Simulate Parent Instruction
    state.parent_decision = {
        "instructions": [{
            "agent": "finance_agent",
            "intent": "log_expense",
            "payload": {
                "merchant": "Starbucks Test",
                "amount": 5.50,
                "category": "Dining"
            }
        }]
    }
    
    new_state = run_finance_node(state)
    
    outputs = [out for out in new_state.agent_outputs if out.agent_name == "finance_agent"]
    for out in outputs:
        print(f"Result: {out.result}")
        
    # Check for XP
    xp_events = [a for a in new_state.planned_actions if a.get("type") == "xp_event"]
    if xp_events:
        print(f"XP Awarded: {xp_events[0]}")
    else:
        print("No XP awarded (Expected if DB missing)")

if __name__ == "__main__":
    test_finance()
