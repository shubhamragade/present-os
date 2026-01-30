
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

# Load environment variables
load_dotenv()

from app.integrations.notion_client import NotionClient
from app.integrations.weather_client import get_forecast
from app.integrations import google_calendar
from app.integrations import gmail_client

def check_notion():
    print("\n--- Checking Notion ---")
    try:
        client = NotionClient.from_env()
        # Try to get active quest as a simple read
        quest = client.get_active_quest()
        print(f"[OK] Notion Connected. Active Quest: {quest.get('name') if quest else 'None'}")
        return True
    except Exception as e:
        print(f"[FAIL] Notion Failed: {e}")
        return False

def check_weather():
    print("\n--- Checking Weather ---")
    try:
        # Default test location
        forecast = get_forecast({"city": "San Francisco"})
        print(f"[OK] Weather Connected. Forecast: {forecast.get('condition')}, Rain Risk: {forecast.get('rain_risk')}")
        return True
    except Exception as e:
        print(f"[FAIL] Weather Failed: {e}")
        return False

def check_calendar():
    print("\n--- Checking Google Calendar ---")
    try:
        # Check upcoming events
        events = google_calendar.list_events(max_results=3)
        print(f"[OK] Calendar Connected. Found {len(events)} upcoming events.")
        for e in events:
            print(f"   - {e.get('summary')} ({e.get('start', {}).get('dateTime') or e.get('start', {}).get('date')})")
        return True
    except Exception as e:
        print(f"[FAIL] Calendar Failed: {e}")
        return False

def check_gmail():
    print("\n--- Checking Gmail ---")
    try:
        # Check unread
        messages = gmail_client.fetch_emails(max_results=3, query="is:unread")
        print(f"[OK] Gmail Connected. Found {len(messages)} unread emails.")
        return True
    except Exception as e:
        print(f"[FAIL] Gmail Failed: {e}")
        return False

def main():
    print("Starting Integration Checks...")
    
    results = {
        "Notion": check_notion(),
        "Weather": check_weather(),
        "Calendar": check_calendar(),
        "Gmail": check_gmail()
    }
    
    print("\n=== SUMMARY ===")
    all_passed = True
    for service, status in results.items():
        icon = "[OK]" if status else "[FAIL]"
        print(f"{icon} {service}")
        if not status:
            all_passed = False
            
    if all_passed:
        print("\nAll systems operational!")
    else:
        print("\nSome integrations failed. Check logs above.")

if __name__ == "__main__":
    main()
