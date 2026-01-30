
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.graph.state import PresentOSState
from app.graph.nodes.email_agent import run_email_node

# Setup Logging
logging.basicConfig(level=logging.INFO)

def test_scan_inbox():
    print("\n>>> TESTING SCAN INBOX <<<")
    state = PresentOSState()
    
    # Simulate Parent Instruction
    state.parent_decision = {
        "instructions": [{
            "agent": "email_agent",
            "intent": "scan_inbox",
            "payload": {"max_results": 3}
        }]
    }
    
    # Run Agent
    new_state = run_email_node(state)
    
    outputs = [out for out in new_state.agent_outputs if out.agent_name == "email_agent"]
    print(f"Outputs count: {len(outputs)}")
    for out in outputs:
        print(f"Output: {out}")

def test_draft_reply():
    print("\n>>> TESTING DRAFT REPLY <<<")
    state = PresentOSState()
    
    # Simulate Parent Instruction with RAG Context
    state.parent_decision = {
        "instructions": [{
            "agent": "email_agent",
            "intent": "draft_reply",
            "payload": {
                "to": "shubhamragade2003@gmail.com",  # Self test
                "subject": "Test Draft from PresentOS Agent",
                "context_notes": "Confirm receiving the upgrade package.",
                "tone_context": "Casual, excited, use emojis.",
                "thread_id": None
            }
        }]
    }
    
    # Run Agent
    new_state = run_email_node(state)
    
    # Fix: agent_outputs is a list of objects, not a dict
    outputs = [out for out in new_state.agent_outputs if out.agent_name == "email_agent"]
    
    print(f"Outputs count: {len(outputs)}")
    for out in outputs:
        print(f"Output: {out}")

if __name__ == "__main__":
    # 1. Test Drafting (Safe, creates draft)
    test_draft_reply()
    
    # 2. Test Scanning (Read only)
    # Uncomment to run against real inbox
    test_scan_inbox()
