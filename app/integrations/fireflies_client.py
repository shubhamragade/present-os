"""
Fireflies.ai API Client (GraphQL)
See: https://docs.fireflies.ai/graphql

Capabilities:
- Fetch transcripts
- Fetch meeting details
- Search meetings
"""

import os
import logging
from typing import Dict, Any, Optional, List
import requests

from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger("presentos.fireflies_client")

FIREFLIES_URL = "https://api.fireflies.ai/graphql"

class FirefliesClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

    @classmethod
    def create_from_env(cls) -> Optional["FirefliesClient"]:
        key = os.getenv("FIREFLIES_API_KEY")
        if not key:
            logger.warning("FIREFLIES_API_KEY not found in .env")
            return None
        return cls(key)

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _query(self, query: str, variables: Dict[str, Any] = None) -> Dict[str, Any]:
        """Execute GraphQL query"""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables

        try:
            resp = requests.post(
                FIREFLIES_URL, 
                json=payload, 
                headers=self.headers, 
                timeout=30
            )
            resp.raise_for_status()
            
            data = resp.json()
            if "errors" in data:
                logger.error(f"Fireflies GraphQL errors: {data['errors']}")
                raise ValueError(f"GraphQL Error: {data['errors'][0]['message']}")
                
            return data.get("data", {})
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Fireflies API connection failed: {e}")
            if e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def get_transcript(self, meeting_id: str) -> Dict[str, Any]:
        """Get full transcript for a meeting"""
        query = """
        query Transcript($id: String!) {
            transcript(id: $id) {
                id
                sentences {
                    index
                    speaker_name
                    speaker_id
                    text
                    created_at
                }
            }
        }
        """
        data = self._query(query, {"id": meeting_id})
        return data.get("transcript", {})

    def get_meeting(self, meeting_id: str) -> Dict[str, Any]:
        """Get processed meeting metadata"""
        query = """
        query Meeting($id: String!) {
            meeting(id: $id) {
                id
                title
                date
                duration
                transcript_url
                audio_url
                summary {
                    keywords
                    action_items
                    overview
                }
                attendees {
                    displayName
                    email
                }
            }
        }
        """
        data = self._query(query, {"id": meeting_id})
        return data.get("meeting", {})
    
    def search_meetings(self, title_contains: str = "", limit: int = 5) -> List[Dict[str, Any]]:
        """Search recent transcripts (meetings)"""
        query = """
        query Transcripts($limit: Int, $title: String) {
            transcripts(limit: $limit, title: $title) {
                id
                title
                date
                duration
            }
        }
        """
        data = self._query(query, {"limit": limit, "title": title_contains})
        return data.get("transcripts", [])
    
    def auto_join_calendar_event(self, calendar_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mock method for auto-join (Fireflies usually auto-joins via Calendar settings).
        This method is kept for architecture compatibility but logs an info message.
        """
        logger.info(f"Auto-join requested for event: {calendar_event.get('title')}")
        return {
            "success": True, 
            "message": "Fireflies scheduled to join via Calendar sync settings",
            "meeting_id": None # ID not known until meeting happens
        }