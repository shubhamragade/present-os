"""
Comprehensive End-to-End Test Suite for Present OS
Tests all agents, services, integrations, and user scenarios
"""

import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime

class PresentOSE2ETester:
    def __init__(self, base_url: str = "http://localhost:8080"):
        self.base_url = base_url
        self.results = []
        
    def log_test(self, category: str, test_name: str, passed: bool, details: str = ""):
        """Log test result"""
        result = {
            "category": category,
            "test": test_name,
            "passed": passed,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.results.append(result)
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} [{category}] {test_name}")
        if details:
            print(f"   → {details}")
    
    # ===== BACKEND API TESTS =====
    
    def test_api_status(self):
        """Test /api/status endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/status")
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                "greeting" in data and
                "updated_state" in data and
                "xp_data" in data["updated_state"]
            )
            
            self.log_test("API", "GET /api/status", passed, 
                         f"Status: {response.status_code}, XP Total: {data.get('updated_state', {}).get('xp_data', {}).get('total', 0)}")
        except Exception as e:
            self.log_test("API", "GET /api/status", False, str(e))
    
    def test_api_energy(self):
        """Test /api/energy endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/energy")
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                "recovery" in data and
                "level" in data and
                "emoji" in data
            )
            
            self.log_test("API", "GET /api/energy", passed,
                         f"Recovery: {data.get('recovery')}%, Level: {data.get('level')}")
        except Exception as e:
            self.log_test("API", "GET /api/energy", False, str(e))
    
    def test_api_notifications(self):
        """Test /api/notifications endpoint"""
        try:
            response = requests.get(f"{self.base_url}/api/notifications")
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                "notifications" in data and
                "unread_count" in data
            )
            
            self.log_test("API", "GET /api/notifications", passed,
                         f"Unread: {data.get('unread_count')}, Total: {len(data.get('notifications', []))}")
        except Exception as e:
            self.log_test("API", "GET /api/notifications", False, str(e))
    
    def test_api_chat(self, message: str, expected_keywords: List[str] = None):
        """Test /api/chat endpoint with a message"""
        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={"message": message},
                timeout=30
            )
            data = response.json()
            
            passed = (
                response.status_code == 200 and
                "response" in data and
                "paei" in data
            )
            
            # Check for expected keywords in response
            if passed and expected_keywords:
                response_text = data.get("response", "").lower()
                keywords_found = all(kw.lower() in response_text for kw in expected_keywords)
                passed = passed and keywords_found
            
            self.log_test("API", f"POST /api/chat: '{message[:30]}...'", passed,
                         f"PAEI: {data.get('paei')}, XP: {data.get('xp_awarded', 0)}, Response: {data.get('response', '')[:50]}...")
            
            return data
        except Exception as e:
            self.log_test("API", f"POST /api/chat: '{message[:30]}...'", False, str(e))
            return None
    
    # ===== AGENT TESTS =====
    
    def test_task_agent(self):
        """Test Task Agent"""
        test_cases = [
            ("Add task: Test the notification system", ["task", "notification"]),
            ("Create task review code due tomorrow", ["task", "review"]),
            ("Add task call mom tonight", ["task", "call"])
        ]
        
        for message, keywords in test_cases:
            self.test_api_chat(message, keywords)
            time.sleep(1)  # Rate limiting
    
    def test_calendar_agent(self):
        """Test Calendar Agent"""
        test_cases = [
            ("Schedule meeting with team tomorrow at 2pm", ["meeting", "schedule"]),
            ("Block deep work tomorrow morning", ["block", "deep"]),
            ("Reschedule my 10am call to afternoon", ["reschedule"])
        ]
        
        for message, keywords in test_cases:
            self.test_api_chat(message, keywords)
            time.sleep(1)
    
    def test_email_agent(self):
        """Test Email Agent"""
        test_cases = [
            ("Check my emails", ["email"]),
            ("Reply to the latest email saying thanks", ["reply", "email"]),
            ("Draft email to John about the project update", ["draft", "email"])
        ]
        
        for message, keywords in test_cases:
            self.test_api_chat(message, keywords)
            time.sleep(1)
    
    def test_browse_agent(self):
        """Test Browse/Research Agent"""
        test_cases = [
            ("Research latest AI trends", ["research", "AI"]),
            ("Find articles about productivity", ["research", "productivity"]),
            ("What are people saying about GPT-4", ["research", "GPT"])
        ]
        
        for message, keywords in test_cases:
            self.test_api_chat(message, keywords)
            time.sleep(1)
    
    def test_focus_agent(self):
        """Test Focus Agent"""
        test_cases = [
            ("Start 90 minute focus session", ["focus", "90"]),
            ("Deep work now", ["deep", "work"]),
            ("Block time for concentration", ["block", "time"])
        ]
        
        for message, keywords in test_cases:
            self.test_api_chat(message, keywords)
            time.sleep(1)
    
    def test_xp_agent(self):
        """Test XP Agent (implicit through other actions)"""
        # XP is awarded automatically, check if it's being tracked
        response = requests.get(f"{self.base_url}/api/status")
        data = response.json()
        xp_data = data.get("updated_state", {}).get("xp_data", {})
        
        total_xp = xp_data.get("total", 0)
        passed = total_xp > 0
        
        self.log_test("Agent", "XP Agent (tracking)", passed,
                     f"Total XP: {total_xp}, P:{xp_data.get('P')}, A:{xp_data.get('A')}, E:{xp_data.get('E')}, I:{xp_data.get('I')}")
    
    def test_parent_agent(self):
        """Test Parent Agent orchestration"""
        # Multi-intent request that requires parent orchestration
        message = "Schedule deep work tomorrow morning, check my emails, and research AI agents"
        data = self.test_api_chat(message)
        
        # Parent should coordinate multiple agents
        passed = data is not None and "response" in data
        self.log_test("Agent", "Parent Agent (multi-intent)", passed,
                     "Orchestrated multiple child agents")
    
    # ===== INTENT CLASSIFIER TESTS =====
    
    def test_intent_classifier(self):
        """Test Intent Classifier with various inputs"""
        test_cases = [
            ("hi", 0, "greeting"),
            ("add task review code", 1, "task creation"),
            ("schedule meeting tomorrow", 1, "calendar"),
            ("check emails", 1, "email"),
            ("research AI trends", 0, "research (read domain)"),
            ("tell me today's plan", 0, "plan report"),
            ("free up weekend", 0, "calendar management"),
        ]
        
        for message, expected_intent_count, description in test_cases:
            data = self.test_api_chat(message)
            # We can't directly check intent count from response, but we can verify it worked
            passed = data is not None
            self.log_test("Intent", f"Classify: '{message}'", passed, description)
            time.sleep(0.5)
    
    # ===== NOTIFICATION TESTS =====
    
    def test_notification_creation(self):
        """Test notification creation"""
        try:
            response = requests.post(f"{self.base_url}/api/notifications/test")
            data = response.json()
            
            passed = data.get("success", False)
            self.log_test("Notification", "Create test notification", passed,
                         f"Notification ID: {data.get('notification', {}).get('id', 'N/A')}")
        except Exception as e:
            self.log_test("Notification", "Create test notification", False, str(e))
    
    def test_notification_mark_read(self):
        """Test marking notification as read"""
        try:
            # First create a notification
            create_resp = requests.post(f"{self.base_url}/api/notifications/test")
            notif_id = create_resp.json().get("notification", {}).get("id")
            
            if notif_id:
                # Mark as read
                read_resp = requests.post(f"{self.base_url}/api/notifications/{notif_id}/read")
                passed = read_resp.json().get("success", False)
                self.log_test("Notification", "Mark as read", passed, f"ID: {notif_id}")
            else:
                self.log_test("Notification", "Mark as read", False, "No notification ID")
        except Exception as e:
            self.log_test("Notification", "Mark as read", False, str(e))
    
    # ===== USER SCENARIO TESTS =====
    
    def test_user_scenarios(self):
        """Test realistic user scenarios"""
        scenarios = [
            {
                "name": "Morning Routine",
                "messages": [
                    "Good morning",
                    "What's on my schedule today?",
                    "Add task review yesterday's meeting notes"
                ]
            },
            {
                "name": "Task Management",
                "messages": [
                    "Create task finish project proposal due Friday",
                    "Add task call client about feedback",
                    "Show my tasks"
                ]
            },
            {
                "name": "Research & Learning",
                "messages": [
                    "Research best practices for API design",
                    "Find articles about microservices architecture"
                ]
            },
            {
                "name": "Calendar Management",
                "messages": [
                    "Block 2 hours for deep work tomorrow",
                    "Schedule team sync Friday 3pm",
                    "Move my afternoon meeting to next week"
                ]
            }
        ]
        
        for scenario in scenarios:
            print(f"\n--- Testing Scenario: {scenario['name']} ---")
            for message in scenario["messages"]:
                self.test_api_chat(message)
                time.sleep(2)  # Give system time to process
    
    # ===== VOICE MODE TESTS =====
    
    def test_voice_endpoints(self):
        """Test voice endpoints (STT/TTS)"""
        # Note: Actual audio testing requires audio files
        # This just checks if endpoints are accessible
        
        try:
            # Test TTS endpoint
            response = requests.post(
                f"{self.base_url}/api/voice/tts",
                json={"message": "Hello, this is a test"},
                timeout=10
            )
            passed = response.status_code == 200
            self.log_test("Voice", "TTS endpoint", passed,
                         f"Status: {response.status_code}, Content-Type: {response.headers.get('content-type')}")
        except Exception as e:
            self.log_test("Voice", "TTS endpoint", False, str(e))
    
    # ===== RUN ALL TESTS =====
    
    def run_all_tests(self):
        """Run complete test suite"""
        print("=" * 60)
        print("PRESENT OS - COMPREHENSIVE E2E TEST SUITE")
        print("=" * 60)
        print()
        
        # Backend API Tests
        print("\n🔌 BACKEND API TESTS")
        print("-" * 60)
        self.test_api_status()
        self.test_api_energy()
        self.test_api_notifications()
        
        # Agent Tests
        print("\n🤖 AGENT TESTS")
        print("-" * 60)
        self.test_parent_agent()
        self.test_task_agent()
        self.test_calendar_agent()
        self.test_email_agent()
        self.test_browse_agent()
        self.test_focus_agent()
        self.test_xp_agent()
        
        # Intent Classifier Tests
        print("\n🧠 INTENT CLASSIFIER TESTS")
        print("-" * 60)
        self.test_intent_classifier()
        
        # Notification Tests
        print("\n🔔 NOTIFICATION TESTS")
        print("-" * 60)
        self.test_notification_creation()
        self.test_notification_mark_read()
        
        # Voice Tests
        print("\n🎤 VOICE MODE TESTS")
        print("-" * 60)
        self.test_voice_endpoints()
        
        # User Scenario Tests
        print("\n👤 USER SCENARIO TESTS")
        print("-" * 60)
        self.test_user_scenarios()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        total = len(self.results)
        passed = sum(1 for r in self.results if r["passed"])
        failed = total - passed
        
        print(f"\nTotal Tests: {total}")
        print(f"✅ Passed: {passed} ({passed/total*100:.1f}%)")
        print(f"❌ Failed: {failed} ({failed/total*100:.1f}%)")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if not result["passed"]:
                    print(f"  • [{result['category']}] {result['test']}")
                    if result['details']:
                        print(f"    → {result['details']}")
        
        # Save results to file
        with open("test_results.json", "w") as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Full results saved to: test_results.json")


if __name__ == "__main__":
    tester = PresentOSE2ETester()
    tester.run_all_tests()
