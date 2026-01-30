# integrations/google_calendar.py
"""
Google Calendar integration adapter.

Provides the functions expected by CalendarService:
- freebusy(calendar_id, time_min, time_max) -> list of busy intervals [{"start": iso, "end": iso}, ...]
- create_event(calendar_id, event, idempotency_key=None) -> created_event dict
- get_event(calendar_id, event_id) -> event dict
- update_event(calendar_id, event_id, updates) -> event dict
- find_conflicts(calendar_id, start, end, exclude_event_id=None) -> list of conflicting events

Notes:
- Requires google-auth, google-auth-oauthlib, google-api-python-client
- Ensure environment variables and token storage as described below.
"""

from __future__ import annotations
import os
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

import google.oauth2.credentials
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors

logger = logging.getLogger("presentos.integrations.google_calendar")
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter("%(asctime)s %(levelname)s: %(message)s"))
    logger.addHandler(ch)
logger.setLevel(logging.INFO)

# Environment variables expected:
# GOOGLE_OAUTH_CLIENT_ID, GOOGLE_OAUTH_CLIENT_SECRET, GOOGLE_OAUTH_REDIRECT_URI
# GOOGLE_CAL_REFRESH_TOKEN (a refresh token for a service account / user)
# NOTE: For multi-user setups implement per-user token storage. This adapter uses a single user refresh token.
# recommended
REDIRECT_URI = os.getenv("GOOGLE_OAUTH_REDIRECT_URI", "urn:ietf:wg:oauth:2.0:oob")
API_SERVICE_NAME = "calendar"
API_VERSION = "v3"

SCOPES = [
    "https://www.googleapis.com/auth/calendar"
]

def _build_credentials_from_refresh_token() -> google.oauth2.credentials.Credentials:
    CLIENT_ID = os.getenv("GOOGLE_OAUTH_CLIENT_ID")
    CLIENT_SECRET = os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
    REFRESH_TOKEN = os.getenv("GMAIL_REFRESH_TOKEN")

    if not (CLIENT_ID and CLIENT_SECRET and REFRESH_TOKEN):
        raise RuntimeError(
            f"Missing Google OAuth configuration:\n"
            f"CLIENT_ID={bool(CLIENT_ID)} "
            f"CLIENT_SECRET={bool(CLIENT_SECRET)} "
            f"REFRESH_TOKEN={bool(REFRESH_TOKEN)}"
        )

    return google.oauth2.credentials.Credentials(
        token=None,
        refresh_token=REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        scopes=[
            "https://www.googleapis.com/auth/calendar",
        ],
    )
def _calendar_service():
    creds = _build_credentials_from_refresh_token()
    return googleapiclient.discovery.build(API_SERVICE_NAME, API_VERSION, credentials=creds, cache_discovery=False)

# -----------------------
# Implementations
# -----------------------
def freebusy(calendar_id: str = "primary", time_min: str = None, time_max: str = None) -> List[Dict[str, Any]]:
    """
    Returns a list of busy intervals for the given calendar in the time window.
    time_min/time_max: ISO strings or None (if None, must be provided by caller)
    """
    service = _calendar_service()
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": calendar_id}],
    }
    try:
        resp = service.freebusy().query(body=body).execute()
        cal = resp.get("calendars", {}).get(calendar_id, {})
        busy = cal.get("busy", [])
        # busy entries are dicts with 'start' and 'end'
        return busy
    except googleapiclient.errors.HttpError as e:
        logger.exception("Google freebusy error: %s", e)
        return []

def create_event(calendar_id: str = "primary", event: Dict[str, Any] = None, idempotency_key: Optional[str] = None) -> Dict[str, Any]:
    """
    Create an event. `event` matches Google calendar event dict fields (summary, start:{dateTime}, end:{dateTime}, attendees).
    We add idempotency via extendedProperties.private.idempotency_key if provided.
    """
    service = _calendar_service()
    event = event or {}
    if idempotency_key:
        event.setdefault("extendedProperties", {}).setdefault("private", {})["idempotency_key"] = idempotency_key
    try:
        created = service.events().insert(calendarId=calendar_id, body=event, sendUpdates="none", conferenceDataVersion=1).execute()
        return created
    except googleapiclient.errors.HttpError as e:
        logger.exception("Google create_event error: %s", e)
        raise

def get_event(calendar_id: str = "primary", event_id: str = "") -> Dict[str, Any]:
    service = _calendar_service()
    try:
        return service.events().get(calendarId=calendar_id, eventId=event_id).execute()
    except googleapiclient.errors.HttpError as e:
        logger.exception("Google get_event error: %s", e)
        raise

def update_event(calendar_id: str = "primary", event_id: str = "", updates: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    updates is a partial event dict; we perform a patch-like update using 'patch' call.
    """
    service = _calendar_service()
    try:
        updated = service.events().patch(calendarId=calendar_id, eventId=event_id, body=updates, sendUpdates="all").execute()
        return updated
    except googleapiclient.errors.HttpError as e:
        logger.exception("Google update_event error: %s", e)
        raise

def find_conflicts(calendar_id: str, start: datetime, end: datetime, exclude_event_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Return list of events that overlap with given interval.
    """
    service = _calendar_service()
    time_min = start.astimezone(timezone.utc).isoformat()
    time_max = end.astimezone(timezone.utc).isoformat()
    try:
        events = service.events().list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max, singleEvents=True, orderBy="startTime").execute()
        items = events.get("items", [])
        if exclude_event_id:
            items = [i for i in items if i.get("id") != exclude_event_id]
        # Filter out events fully outside overlap (Google already restricts by timeMin/timeMax)
        return items
    except googleapiclient.errors.HttpError as e:
        logger.exception("Google find_conflicts error: %s", e)
        return []

def list_events(calendar_id: str = "primary", max_results: int = 10, time_min: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    List upcoming events for a specific calendar.
    """
    service = _calendar_service()
    if not time_min:
        time_min = datetime.now(timezone.utc).isoformat()
    
    try:
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            maxResults=max_results,
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        return events_result.get('items', [])
    except googleapiclient.errors.HttpError as e:
        logger.error(f"Failed to list events: {e}")
        return []
