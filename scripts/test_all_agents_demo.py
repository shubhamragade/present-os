"""
Present OS - Comprehensive Agent Test Script
Tests all agents and generates a report.
Run with: python scripts/test_all_agents_demo.py
"""

import requests
import json
import time
import sys
from datetime import datetime

BASE_URL = "http://localhost:8080"

# ============================================
# AGENT TEST SCENARIOS
# ============================================

AGENT_TESTS = {
    "Task Agent": [
        "Add task call mom tonight",
        "Show my tasks",
        "Create task review quarterly report due Friday",
    ],
    "Calendar Agent": [
        "What's on my schedule today?",
        "Schedule team meeting tomorrow at 2 PM",
        "Block deep work tomorrow morning 9 to 11",
    ],
    "Weather Agent": [
        "What's the weather in Pune?",
        "Is it good for outdoor work today?",
        "Weather forecast for Mumbai",
    ],
    "XP Agent": [
        "Show my XP status",
        "What's my current level?",
        "How much XP do I have?",
    ],
    "Email Agent": [
        "Check my emails",
        "Show unread emails",
        "Any important emails today?",
    ],
    "Focus Agent": [
        "Start a 25 minute focus session",
        "Block time for concentration this afternoon",
        "I need deep work time tomorrow",
    ],
    "Finance Agent": [
        "Show my budget summary",
        "What bills are due this month?",
        "Track my expenses",
    ],
    "Contact Agent": [
        "Show contact for John",
        "Who is my contact at Microsoft?",
        "Add note for contact: met at conference",
    ],
    "Research Agent": [
        "Research best practices for API design 2026",
        "Find information about AI productivity tools",
        "Look up latest trends in no-code platforms",
    ],
    "Plan Report Agent": [
        "What's my plan for today?",
        "Give me a daily summary",
        "What should I focus on today?",
    ],
}


def test_agent(agent_name, queries):
    """Test a specific agent with multiple queries"""
    print(f"\n{'='*60}")
    print(f"TESTING: {agent_name}")
    print(f"{'='*60}")
    
    results = []
    
    for query in queries:
        print(f"\n>>> Query: {query}")
        try:
            start = time.time()
            response = requests.post(
                f"{BASE_URL}/api/chat",
                json={"message": query},
                timeout=60
            )
            duration = time.time() - start
            
            if response.status_code == 200:
                data = response.json()
                resp_text = data.get("response", "")[:200]
                print(f"    [PASS] ({duration:.1f}s)")
                print(f"    Response: {resp_text}...")
                results.append({"query": query, "status": "PASS", "time": duration})
            else:
                print(f"    [FAIL] Status: {response.status_code}")
                results.append({"query": query, "status": "FAIL", "error": response.text})
                
        except Exception as e:
            print(f"    [ERROR] {str(e)[:100]}")
            results.append({"query": query, "status": "ERROR", "error": str(e)})
        
        time.sleep(1)  # Rate limiting
    
    return results


def test_voice_system():
    """Test the voice TTS endpoint"""
    print(f"\n{'='*60}")
    print(f"TESTING: Voice System (Murf TTS)")
    print(f"{'='*60}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/voice/tts",
            json={"message": "Hello! This is PresentOS speaking."},
            timeout=30
        )
        
        if response.status_code == 200 and len(response.content) > 1000:
            print(f"    [PASS] TTS generated {len(response.content)} bytes of audio")
            return {"status": "PASS", "bytes": len(response.content)}
        else:
            print(f"    [FAIL] TTS failed or returned small response")
            return {"status": "FAIL"}
    except Exception as e:
        print(f"    [ERROR] {str(e)}")
        return {"status": "ERROR", "error": str(e)}


def run_all_tests():
    """Run all agent tests and generate a report"""
    print("\n" + "="*60)
    print("PRESENT OS - COMPREHENSIVE AGENT TEST")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    # Check server is running
    try:
        requests.get(f"{BASE_URL}/api/status", timeout=5)
    except:
        print("\n[ERROR] Server not running! Start with:")
        print("  uvicorn app.api:app --host 0.0.0.0 --port 8080")
        sys.exit(1)
    
    all_results = {}
    
    # Test each agent
    for agent_name, queries in AGENT_TESTS.items():
        all_results[agent_name] = test_agent(agent_name, queries)
    
    # Test voice system
    all_results["Voice System"] = [test_voice_system()]
    
    # Generate summary report
    print("\n" + "="*60)
    print("TEST SUMMARY REPORT")
    print("="*60)
    
    total_pass = 0
    total_fail = 0
    total_error = 0
    
    for agent, results in all_results.items():
        passed = sum(1 for r in results if r.get("status") == "PASS")
        failed = sum(1 for r in results if r.get("status") == "FAIL")
        errors = sum(1 for r in results if r.get("status") == "ERROR")
        
        status = "[PASS]" if failed == 0 and errors == 0 else "[ISSUES]"
        print(f"{status} {agent}: {passed}/{len(results)} passed")
        
        total_pass += passed
        total_fail += failed
        total_error += errors
    
    print("\n" + "-"*40)
    total = total_pass + total_fail + total_error
    print(f"TOTAL: {total_pass}/{total} tests passed")
    print(f"       {total_fail} failed, {total_error} errors")
    print("-"*40)
    
    # Save results to file
    with open("agent_test_report.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": total,
                "passed": total_pass,
                "failed": total_fail,
                "errors": total_error
            },
            "results": all_results
        }, f, indent=2)
    
    print("\nReport saved to: agent_test_report.json")
    
    return total_fail == 0 and total_error == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
