"""
Golden Test v3 - Full System Verification
Verifies:
1. Intent Classification (including Greetings)
2. Agent Coordination
3. Standardized Agent Outputs
4. Martin Persona (Natural Response + XP)
5. TTS Integration (Murf AI)
"""

import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.graph.state import PresentOSState
from app.graph.graph_executor import build_presentos_graph
from app.api import MurfClient

def run_test_case(name: str, input_text: str):
    print(f"\n{'='*50}")
    print(f"TEST CASE: {name}")
    print(f"INPUT: {input_text}")
    print(f"{'='*50}")

    graph = build_presentos_graph()
    state = PresentOSState()
    state.input_text = input_text
    
    # Run graph
    result = graph.invoke(state)
    
    print(f"\n--- INTENT CLASSIFICATION ---")
    print(f"Intents: {[i.intent for i in result.intent.intents]}")
    print(f"Read Domains: {result.intent.read_domains}")
    print(f"Explanation: {result.intent.explanation}")

    print(f"\n--- AGENT OUTPUTS ---")
    for out in (result.agent_outputs or []):
        print(f"Agent: {out.agent_name} | Success: {out.result.get('success', out.result.get('status'))}")
        print(f"  Result: {out.result}")

    print(f"\n--- MARTIN'S RESPONSE ---")
    print(result.final_response)
    
    print(f"\n--- TTS VERIFICATION ---")
    murf = MurfClient.create_from_env()
    if murf:
        # Just test first 50 chars to verify connectivity
        audio = murf.synthesize(result.final_response[:50])
        if audio:
            print("✅ Murf TTS synthesis successful.")
        else:
            print("❌ Murf TTS synthesis failed.")
    else:
        print("⚠️ Murf Client not configured correctly.")

if __name__ == "__main__":
    # Test 1: Complex Coordination (Task + Calendar + Research)
    run_test_case(
        "Complex Coordination",
        "Tomorrow morning schedule deep work 9-12, move my 10am if possible, and check if my camera is still on sale on Amazon."
    )
    
    # Test 2: Greeting
    run_test_case(
        "Greeting",
        "Hi Martin, how's it going?"
    )
    
    # Test 3: Finance + Task
    run_test_case(
        "Finance + Task",
        "Reply to the electricity bill saying I'll pay next week and add a task to check my portfolio Sunday."
    )
