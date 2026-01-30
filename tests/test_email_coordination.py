"""
Test Email + Task Coordination
Tests the sophisticated multi-agent scenario from the demo
"""

import requests
import json

BASE_URL = "http://localhost:8080"

def test_email_task_coordination():
    """
    Test: "Reply to electricity bill — say I'll pay next week and ask for extension"
    
    Expected:
    - Email sent with extension request
    - Task created in Notion
    - XP awarded (Administrator)
    """
    
    print("=" * 70)
    print("TESTING EMAIL + TASK COORDINATION")
    print("=" * 70)
    
    query = "Reply to electricity bill — say I'll pay next week and ask for extension"
    
    print(f"\n📝 Query: {query}")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": query},
            timeout=60  # Longer timeout for multi-agent
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"🤖 PAEI: {data.get('paei')}")
            print(f"⭐ XP: {data.get('xp_awarded', 0)}")
            print(f"\n💬 Response:")
            print(data.get('response', ''))
            
            # Check for expected elements
            response_text = data.get('response', '').lower()
            
            checks = {
                "Email sent": 'email' in response_text and ('sent' in response_text or 'draft' in response_text),
                "Task created": 'task' in response_text or 'added' in response_text,
                "XP awarded": 'xp' in response_text or data.get('xp_awarded', 0) > 0,
                "Administrator role": data.get('paei') == 'A' or 'administrator' in response_text
            }
            
            print(f"\n✓ Coordination Checks:")
            for check, passed in checks.items():
                status = "✅" if passed else "⚠️"
                print(f"  {status} {check}: {passed}")
            
            # Overall success
            if all(checks.values()):
                print(f"\n🎉 FULL COORDINATION SUCCESS!")
            else:
                print(f"\n⚠️ Partial success - some elements missing")
                
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"Error: {response.text[:200]}")
            
    except requests.exceptions.Timeout:
        print(f"⏱️ TIMEOUT - Multi-agent coordination took > 60 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")


def test_simple_email_send():
    """Test simple email sending"""
    
    print("\n" + "=" * 70)
    print("TESTING SIMPLE EMAIL SEND")
    print("=" * 70)
    
    query = "send email to shubhamragade2003@gmail.com saying test from PresentOS"
    
    print(f"\n📝 Query: {query}")
    print("-" * 70)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/chat",
            json={"message": query},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"🤖 PAEI: {data.get('paei')}")
            print(f"⭐ XP: {data.get('xp_awarded', 0)}")
            print(f"\n💬 Response:")
            print(data.get('response', ''))
            
            response_text = data.get('response', '').lower()
            
            if 'email sent' in response_text or 'sent to' in response_text:
                print(f"\n✅ Email sent successfully!")
            elif 'draft' in response_text:
                print(f"\n📝 Draft created (not sent)")
            else:
                print(f"\n⚠️ Unclear if email was sent")
                
        else:
            print(f"❌ Status: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")


if __name__ == "__main__":
    print("\n🚀 Starting Email Functionality Tests\n")
    
    # Test 1: Simple email send
    test_simple_email_send()
    
    print("\n" + "=" * 70)
    input("\nPress Enter to continue to coordination test...")
    
    # Test 2: Email + Task coordination
    test_email_task_coordination()
    
    print("\n" + "=" * 70)
    print("✅ All tests complete!")
    print("=" * 70)
