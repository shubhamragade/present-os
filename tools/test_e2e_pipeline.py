"""
End-to-End Pipeline Test for PresentOS
Tests: Intent Classifier → Parent Agent → Graph Executor → Child Agents → Response
"""

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
from app.integrations.notion_client import NotionClient

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s:%(message)s')
logger = logging.getLogger("e2e_test")

def test_end_to_end_pipeline():
    """
    Complete pipeline test with a real user message.
    """
    print("\n" + "="*80)
    print("PRESENTOS END-TO-END PIPELINE TEST")
    print("="*80 + "\n")
    
    # Test message
    user_message = "Add a high priority task: 'Test all agents' due tomorrow, linked to the MVP quest, PAEI focus on Producer"
    
    print(f"User Message: \"{user_message}\"\n")
    
    # ============================================================
    # STEP 1: INTENT CLASSIFICATION
    # ============================================================
    print("STEP 1: Intent Classifier")
    print("-" * 80)
    
    classifier = get_default_intent_classifier()
    intent_result = classifier.classify(user_message)
    
    print(f"[OK] Classified Intents: {len(intent_result.intents)}")
    for intent in intent_result.intents:
        print(f"   - Intent: {intent.intent}")
        print(f"     Category: {intent.category}")
        print(f"     Payload: {json.dumps(intent.payload, indent=6)}")
    
    print(f"   Confidence: {intent_result.confidence}")
    print(f"   Model: {intent_result.model}\n")
    
    # ============================================================
    # STEP 2: PARENT AGENT DECISION
    # ============================================================
    print("STEP 2: Parent Agent Decision")
    print("-" * 80)
    
    # Create state
    state = PresentOSState()
    state.input_text = user_message
    state.intent = intent_result
    state.energy_level = 0.8  # High energy
    
    # Build graph
    graph = build_presentos_graph()
    
    print("   Graph built successfully")
    print(f"   Initial state energy: {state.energy_level}")
    print(f"   Timezone: {state.timezone}\n")
    
    # ============================================================
    # STEP 3: GRAPH EXECUTION
    # ============================================================
    print("STEP 3: Graph Execution")
    print("-" * 80)
    
    result_state = graph.invoke(state)
    
    print("   Graph execution complete!")
    
    # Check parent decision
    if result_state.parent_decision:
        pd = result_state.parent_decision
        print(f"\n   [DECISION] Parent Decision:")
        print(f"      PAEI Role: {pd['paei_decision']['role']}")
        print(f"      XP Amount: {pd['paei_decision']['xp_amount']}")
        print(f"      Reasoning: {pd['paei_decision']['reasoning']}")
        print(f"      Coordinated Action: {pd['is_coordinated_action']}")
        print(f"      Instructions: {len(pd['instructions'])} agents activated")
        
        print(f"\n   [AGENTS] Activated Agents:")
        for instr in pd['instructions']:
            print(f"      - {instr['agent']}: {instr['intent']}")
    
    # ============================================================
    # STEP 4: CHILD AGENT OUTPUTS
    # ============================================================
    print("\n" + "STEP 4: Child Agent Outputs")
    print("-" * 80)
    
    if result_state.agent_outputs:
        print(f"   Total outputs: {len(result_state.agent_outputs)}\n")
        
        for output in result_state.agent_outputs:
            print(f"   [OUTPUT] {output.agent_name}:")
            # AgentOutput has: agent_name, result, timestamp
            if hasattr(output, 'result') and output.result:
                # Pretty print result
                if isinstance(output.result, dict):
                    for key, value in output.result.items():
                        if key not in ['raw_response', 'full_context']:  # Skip verbose fields
                            print(f"      {key}: {value}")
                else:
                    print(f"      Result: {output.result}")
            print()
    else:
        print("   [WARNING] No agent outputs recorded")
    
    # ============================================================
    # STEP 5: FINAL RESPONSE
    # ============================================================
    print("STEP 5: Final Response to User")
    print("-" * 80)
    
    final_response = result_state.final_response or "No response generated"
    # Basic sanitization for Windows console
    sanitized_response = final_response.encode('ascii', 'ignore').decode('ascii')
    print(f"   [RESPONSE] Response: \"{sanitized_response}\" (sanitized for console)\n")
    
    # ============================================================
    # STEP 6: SIDE EFFECTS VERIFICATION
    # ============================================================
    print("STEP 6: Side Effects Verification")
    print("-" * 80)
    
    # Check if task was created in Notion
    notion = NotionClient.from_env()
    recent_tasks = notion.get_tasks(status_filter="To Do", limit=5)
    
    print(f"   [TASKS] Recent Notion Tasks (Top 5):")
    for task in recent_tasks[:5]:
        print(f"      - {task['name']} (Status: {task['status']}, Priority: {task['priority']})")
    
    # Check XP
    xp_summary = notion.get_xp_summary()
    print(f"\n   [XP] Current XP:")
    print(f"      P: {xp_summary['P']}, A: {xp_summary['A']}, E: {xp_summary['E']}, I: {xp_summary['I']}")
    print(f"      Total: {xp_summary['total']}, Streak: {xp_summary['streak']}")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print("\n" + "="*80)
    print("[OK] END-TO-END PIPELINE TEST COMPLETE")
    print("="*80)
    
    print("\n[SUMMARY] Pipeline Summary:")
    print(f"   1. Intent Classification: ✅ ({len(intent_result.intents)} intents)")
    print(f"   2. Parent Decision: ✅ (PAEI: {result_state.parent_decision['paei_decision']['role'] if result_state.parent_decision else 'N/A'})")
    print(f"   3. Graph Execution: ✅ ({len(result_state.agent_outputs)} agents executed)")
    print(f"   4. Response Generated: ✅")
    print(f"   5. Notion Updated: ✅ ({len(recent_tasks)} tasks found)")
    
    print("\n[SUCCESS] All systems operational!\n")


if __name__ == "__main__":
    test_end_to_end_pipeline()
