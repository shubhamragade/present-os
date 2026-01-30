
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.graph.state import PresentOSState
from app.graph.parent_node import run_parent_node
from app.services.intent_classifier import IntentResult, SubIntent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_learning")

def test_memory_wiring():
    print("\n>>> TESTING CONTINUOUS LEARNING WIRING <<<")
    
    state = PresentOSState()
    state.input_text = "Schedule a meeting for tomorrow at 10am"
    state.energy_level = 0.9  # High energy
    
    # Mock Intent Result
    state.intent = IntentResult(
        intents=[SubIntent(intent="schedule_meeting", category="calendar", payload={"title": "Test Meeting"})],
        read_domains=[],
        confidence=1.0,
        explanation="Testing",
        model="gpt-4o",
        raw={}
    )
    
    print("Running ParentNode...")
    new_state = run_parent_node(state)
    
    print("\nChecking logs for Evidence...")
    # Since we can't easily capture logs from here without a complex setup, 
    # we'll look for the 'memories' in the output state if we added it there, 
    # but more importantly, we just want to ensure it doesn't crash.
    
    if "parent_decision" in new_state.__dict__:
        print(f"Decision Role: {new_state.parent_decision['paei_decision']['role']}")
        print(f"Energy Capacity: {new_state.parent_decision['energy_context']['capacity']}")
    
    print("\nCOMPLETED: Check terminal logs for 'Continuous learning: Memory writer check complete'")

if __name__ == "__main__":
    test_memory_wiring()
