"""
Comprehensive End-to-End System Test for Present OS
Tests all agents, services, and user scenarios
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# Encoding fix for Windows
sys.stdout.reconfigure(encoding='utf-8')

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

results = []

def log(status, category, message):
    icon = "[PASS]" if status else "[FAIL]"
    print(f"{icon} [{category}] {message}")
    results.append({"status": status, "category": category, "message": message})

def test_imports():
    """Test all agent and service imports"""
    print("\n" + "="*60)
    print("1. IMPORT TESTS - All Agents & Services")
    print("="*60)
    
    # Agents
    agents = [
        ("app.graph.nodes.task_agent", "run_task_node", "TaskAgent"),
        ("app.graph.nodes.calendar_agent", "run_calendar_node", "CalendarAgent"),
        ("app.graph.nodes.email_agent", "run_email_node", "EmailAgent"),
        ("app.graph.nodes.weather_agent", "run_weather_node", "WeatherAgent"),
        ("app.graph.nodes.xp_agent", "run_xp_node", "XPAgent"),
        ("app.graph.nodes.focus_agent", "run_focus_node", "FocusAgent"),
        ("app.graph.nodes.contact_agent", "run_contact_node", "ContactAgent"),
        ("app.graph.nodes.research_agent", "run_research_node", "ResearchAgent"),
        ("app.graph.nodes.finance_agent", "run_finance_node", "FinanceAgent"),
        ("app.graph.nodes.fireflies_agent", "run_fireflies_node", "FirefliesAgent"),
        ("app.graph.nodes.browser_agent", "run_browser_node", "BrowserAgent"),
        ("app.graph.nodes.plan_report_agent", "run_plan_report_node", "PlanReportAgent"),
        ("app.graph.nodes.quest_agent", "run_quest_node", "QuestAgent"),
        ("app.graph.nodes.map_agent", "run_map_node", "MAPAgent"),
    ]
    
    for module, func, name in agents:
        try:
            mod = __import__(module, fromlist=[func])
            getattr(mod, func)
            log(True, "Agent", f"{name} imported successfully")
        except Exception as e:
            log(False, "Agent", f"{name} import failed: {e}")
    
    # Core nodes
    try:
        from app.graph.parent_node import run_parent_node
        log(True, "Core", "ParentNode imported successfully")
    except Exception as e:
        log(False, "Core", f"ParentNode import failed: {e}")
    
    try:
        from app.graph.parent_response_node import run_parent_response_node
        log(True, "Core", "ParentResponseNode imported successfully")
    except Exception as e:
        log(False, "Core", f"ParentResponseNode import failed: {e}")
    
    try:
        from app.graph.graph_executor import build_presentos_graph
        log(True, "Core", "GraphExecutor imported successfully")
    except Exception as e:
        log(False, "Core", f"GraphExecutor import failed: {e}")

def test_integrations():
    """Test integration clients"""
    print("\n" + "="*60)
    print("2. INTEGRATION TESTS - External Services")
    print("="*60)
    
    # NotionClient
    try:
        from app.integrations.notion_client import NotionClient
        nc = NotionClient.from_env()
        log(True, "Integration", "NotionClient connected successfully")
    except Exception as e:
        log(False, "Integration", f"NotionClient failed: {e}")
    
    # FinanceClient
    try:
        from app.integrations.finance_client import FinanceClient
        log(True, "Integration", "FinanceClient imported successfully")
    except Exception as e:
        log(False, "Integration", f"FinanceClient failed: {e}")
    
    # GmailClient (uses functions, not class)
    try:
        from app.integrations.gmail_client import fetch_emails, create_draft, send_email
        log(True, "Integration", "GmailClient (functions) imported successfully")
    except Exception as e:
        log(False, "Integration", f"GmailClient failed: {e}")
    
    # GoogleCalendar (uses functions, not class)
    try:
        from app.integrations.google_calendar import freebusy, create_event, list_events
        log(True, "Integration", "GoogleCalendar (functions) imported successfully")
    except Exception as e:
        log(False, "Integration", f"GoogleCalendarClient failed: {e}")

def test_services():
    """Test services"""
    print("\n" + "="*60)
    print("3. SERVICE TESTS")
    print("="*60)
    
    try:
        from app.services.calendar_service import CalendarService
        log(True, "Service", "CalendarService imported successfully")
    except Exception as e:
        log(False, "Service", f"CalendarService failed: {e}")
    
    try:
        from app.services.paei_engine import PAEIDecisionEngine, get_paei_decision
        log(True, "Service", "PAEIEngine imported successfully")
    except Exception as e:
        log(False, "Service", f"PAEIEngine failed: {e}")

def test_graph_build():
    """Test building the full graph"""
    print("\n" + "="*60)
    print("4. GRAPH BUILD TEST")
    print("="*60)
    
    try:
        from app.graph.graph_executor import build_presentos_graph
        graph = build_presentos_graph()
        log(True, "Graph", "Full graph built successfully")
        return graph
    except Exception as e:
        log(False, "Graph", f"Graph build failed: {e}")
        return None

def test_e2e_flow(graph):
    """Test end-to-end flow with various user inputs"""
    print("\n" + "="*60)
    print("5. END-TO-END FLOW TESTS")
    print("="*60)
    
    if graph is None:
        log(False, "E2E", "Skipped - graph not available")
        return
    
    from app.graph.state import PresentOSState
    
    test_cases = [
        ("hi", "Greeting"),
        ("What's my plan for today?", "Plan Report"),
        ("Check the weather in San Francisco", "Weather Check"),
        ("Create task review meeting notes", "Task Creation"),
        ("Schedule meeting tomorrow at 3pm", "Calendar Scheduling"),
    ]
    
    for input_text, description in test_cases:
        try:
            state = PresentOSState(
                input_text=input_text,
                user_id="test_user"
            )
            final_state = graph.invoke(state)
            
            has_response = final_state.final_response and len(final_state.final_response) > 5
            log(has_response, "E2E", f"{description}: '{input_text[:30]}...'")
            
            if has_response:
                print(f"       Response: {final_state.final_response[:80]}...")
                print(f"       Agents: {final_state.activated_agents}")
            
        except Exception as e:
            log(False, "E2E", f"{description} failed: {str(e)[:50]}")

def print_summary():
    """Print test summary"""
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results if r["status"])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed} ({passed/total*100:.1f}%)")
    print(f"Failed: {failed} ({failed/total*100:.1f}%)")
    
    if failed > 0:
        print("\nFailed Tests:")
        for r in results:
            if not r["status"]:
                print(f"  - [{r['category']}] {r['message']}")
    
    return failed == 0

def main():
    print("="*60)
    print("PRESENT OS - COMPREHENSIVE SYSTEM TEST")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("="*60)
    
    test_imports()
    test_integrations()
    test_services()
    graph = test_graph_build()
    test_e2e_flow(graph)
    
    success = print_summary()
    
    if success:
        print("\n*** ALL TESTS PASSED ***")
        return 0
    else:
        print("\n*** SOME TESTS FAILED ***")
        return 1

if __name__ == "__main__":
    sys.exit(main())
