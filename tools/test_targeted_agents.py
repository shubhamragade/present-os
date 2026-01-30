
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import json

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.graph.state import PresentOSState
from app.graph.graph_executor import build_presentos_graph
from app.services.intent_classifier import get_default_intent_classifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agent_test")

def run_test(message):
    print(f"\nTRACING: {message}")
    print("-" * 50)
    
    state = PresentOSState()
    state.input_text = message
    
    # Init classifier
    classifier = get_default_intent_classifier()
    state.intent = classifier.classify(message)
    
    # Build and run graph
    graph = build_presentos_graph()
    result = graph.invoke(state)
    
    # Print outputs
    for output in result.agent_outputs:
        print(f"Agent: {output.agent_name}")
        print(f"Result: {json.dumps(output.result, indent=2)}")
    
    # Sanitize and print final response
    resp = result.final_response or "No response"
    print(f"Response: {resp.encode('ascii', 'ignore').decode('ascii')}")

if __name__ == "__main__":
    print("STARTING TARGETED AGENT TESTS")
    
    # Test 1: Focus
    run_test("Start a 90 minute deep work session for coding")
    
    # Test 2: Quest
    run_test("Create a new quest: 'Project Zero' to build the first agentic OS by December")
