
import sys
import os
import logging
from pathlib import Path
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).resolve().parent.parent))
load_dotenv()

from app.integrations.fireflies_client import FirefliesClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("test_fireflies")

def test_fireflies():
    print("\n>>> TESTING FIREFLIES CLIENT <<<")
    
    client = FirefliesClient.create_from_env()
    if not client:
        print("❌ SKIPPING: No FIREFLIES_API_KEY in .env")
        return

    try:
        print("1. Searching recent meetings...")
        meetings = client.search_meetings(limit=3)
        print(f"✅ Found {len(meetings)} meetings")
        for m in meetings:
            print(f"   - {m.get('title')} ({m.get('date')}) [ID: {m.get('id')}]")
            
        if meetings:
            latest_id = meetings[0]['id']
            print(f"\n2. Fetching details for ID: {latest_id}")
            details = client.get_meeting(latest_id)
            summary = details.get('summary', {})
            print(f"✅ Summary Overview: {str(summary.get('overview'))[:100]}...")
            
    except Exception as e:
        print(f"❌ API Error: {e}")

if __name__ == "__main__":
    test_fireflies()
