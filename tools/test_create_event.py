
import logging
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from app.integrations import google_calendar
from dotenv import load_dotenv

load_dotenv()

def test_create_event():
    print("\n------------------------------")
    print("TEST: Creating Calendar Event")
    print("------------------------------")

    # Event 1 hour from now
    start_time = datetime.now() + timedelta(hours=1)
    end_time = start_time + timedelta(minutes=30)
    
    event_payload = {
        "summary": "PresentOS Test Event 🤖",
        "description": "This is a test event created to verify Write permissions.",
        "start": {
            "dateTime": start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC",
        },
    }

    try:
        print(f"Creating event: {event_payload['summary']}")
        result = google_calendar.create_event("primary", event_payload)
        
        print(f"✅ SUCCESS! Event created.")
        print(f"ID: {result.get('id')}")
        print(f"Link: {result.get('htmlLink')}")
        return True
    except Exception as e:
        print(f"❌ FAILED to create event: {e}")
        return False

if __name__ == "__main__":
    test_create_event()
