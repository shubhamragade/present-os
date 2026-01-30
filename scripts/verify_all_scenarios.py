
import asyncio
import logging
import sys
import os
from pathlib import Path

# Add root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Mock settings if needed, or rely on .env
from dotenv import load_dotenv
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.ERROR) # Quiet logs

from app.graph.parent_node import ParentNode
from app.graph.state import PresentOSState
from app.services.intent_classifier import IntentClassifier

# Initialize Core Components
print("Initializing System...")
try:
    parent = ParentNode()
    classifier = IntentClassifier(model="gpt-4o-mini")
    print("System Initialized")
except Exception as e:
    print(f"System Init Failed: {e}")
    sys.exit(1)

# Scenarios from User's Script
SCENARIOS = [
    # Task Agent
    "Add task call mom tonight",
    "Create task review quarterly report due Friday",
    "Show my tasks",
    
    # Calendar Agent
    "What's on my schedule today?",
    "Schedule team meeting tomorrow at 3 PM",
    "Block deep work tomorrow morning 9 to 11",
    
    # Weather Agent
    "What's the weather in Pune?",
    "Is it good weather for outdoor work today?",
    
    # XP Agent
    "Show my XP status",
    "How much XP do I have?",
    
    # Email Agent
    "Check my emails",
    "Draft a reply to the last email saying thank you",
    
    # Focus Agent
    "Start a 25 minute focus session",
    
    # Finance Agent
    "Show my budget summary",
    
    # Contact Agent
    "Show contact for John",
    "Add note to John: met at tech conference",
    
    # Research Agent
    "Research best practices for API design 2026",
    
    # Plan Report
    "What's my plan for today?"
]

print(f"\nRunning {len(SCENARIOS)} Scenario Tests...\n")

success_count = 0

for i, query in enumerate(SCENARIOS, 1):
    print(f"Test {i}: '{query}'")
    
    try:
        # 1. Classify
        intent_result = classifier.classify(query)
        # print(f"   Intent: {[i.intent for i in intent_result.intents]} + {intent_result.read_domains}")
        
        # 2. Mimic State
        state = PresentOSState(
            input_text=query,
            intent=intent_result,
            user_id="test_user",
            timezone="Asia/Kolkata"
        )
        
        # 3. Component Execution (Parent Logic Only - Don't trigger side effects if possible, but ParentNode builds instructions)
        # We can run ParentNode to see the *Instructions* generated
        
        # Mock weather snapshot for consistent testing
        state.weather_snapshot = {
            "current": {"temp_c": 28, "condition": "Sunny", "wind_speed_knots": 10},
            "surf_analysis": {"condition_type": "good_surf", "score": 8}
        }
        
        result_state = parent(state)
        
        decision = result_state.parent_decision
        
        if decision:
            unified = decision.get("unified_response", "No response")
            instrs = decision.get("instructions", [])
            agents = [ins["agent"] for ins in instrs]
            
            print(f"   Agents: {agents}")
            print(f"   Response: {unified}")
            success_count += 1
        else:
            print("   No Decision Generated")

    except Exception as e:
        print(f"   Error: {e}")

print(f"\napps Summary: {success_count}/{len(SCENARIOS)} Scenarios Simulation Passed")
