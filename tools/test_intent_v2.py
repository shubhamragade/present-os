
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.services.intent_classifier import get_default_intent_classifier

def test_classifier():
    print("🤖 TESTING INTENT CLASSIFIER V2 (Structured Outputs) 🤖\n")
    
    classifier = get_default_intent_classifier()
    
    test_inputs = [
        "Schedule a meeting with the team tomorrow to discuss strategy",
        "Research the best LLM frameworks for 2026",
        "Add a task to buy milk urgently",
        "What is the weather like?"
    ]
    
    for text in test_inputs:
        print(f"User: \"{text}\"")
        try:
            result = classifier.classify(text)
            print("✅ Result:")
            print(f"  Confidence: {result.confidence}")
            print(f"  Intents: {len(result.intents)}")
            for i in result.intents:
                print(f"    - [{i.category}] {i.intent} (Hint: {i.paei_hint})")
            print(f"  Read Domains: {result.read_domains}")
            print(f"  PAEI Hint (Global): {result.paei_hint}")
            print("-" * 40)
        except Exception as e:
            print(f"❌ FAILED: {e}")
            print("-" * 40)

if __name__ == "__main__":
    test_classifier()
