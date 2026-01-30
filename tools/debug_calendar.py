
import os
import logging
from dotenv import load_dotenv
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load env
load_dotenv()

# Setup Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("debug_calendar")

def debug_calendar():
    print("\n------------------------------")
    print("DEBUG: Google Calendar Connect")
    print("------------------------------")
    
    CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")

    print(f"Client ID present: {bool(CLIENT_ID)}")
    print(f"Client Secret present: {bool(CLIENT_SECRET)}")
    print(f"Refresh Token present: {bool(REFRESH_TOKEN)}")

    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        print("❌ Missing credentials.")
        return

    # SCOPE: Testing with ONLY the one the user confirmed
    SCOPES = ["https://www.googleapis.com/auth/calendar"]

    creds = Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=SCOPES
    )

    try:
        print("Attempting to build service...")
        service = build("calendar", "v3", credentials=creds)
        
        print("Attempting API Call (list events)...")
        # Just list 1 event to prove access
        events_result = service.events().list(
            calendarId='primary', maxResults=1
        ).execute()
        
        print("✅ SUCCESS! API Call Worked.")
        items = events_result.get('items', [])
        print(f"Found {len(items)} events.")
        
    except HttpError as e:
        print(f"\n❌ API Error: {e}")
        print(f"Status Code: {e.resp.status}")
        content = e.content.decode('utf-8')
        print(f"Error Content: {content}")
        
        if "accessNotConfigured" in content or "Project has not enabled the API" in content:
            print("\n>>> DIAGNOSIS: The 'Google Calendar API' is NOT enabled in your Cloud Console.")
        elif "insufficient permissions" in content or "Invalid Claims" in content:
            print("\n>>> DIAGNOSIS: The token lacks the 'https://www.googleapis.com/auth/calendar' scope.")
            
    except Exception as e:
        print(f"\n❌ Unexpected Error: {e}")

if __name__ == "__main__":
    debug_calendar()
