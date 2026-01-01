# app/integrations/gmail_client.py - FIXED
"""
Gmail integration adapter for PresentOS.

STRICT RULES (PDF-COMPLIANT):
- This file does NOT contain intelligence, intent detection, or keyword logic
- This file ONLY talks to Gmail API
- NEVER sends emails automatically
- Draft-only operations
- Email Agent + LLM decides WHAT to do, this client only EXECUTES

Capabilities:
- Fetch unread emails
- Fetch full email content
- Create Gmail drafts (reply or new)
"""

from __future__ import annotations

import os
import base64
import logging
from typing import Dict, Any, List, Optional

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger("presentos.gmail")
logger.setLevel(logging.INFO)

# ------------------------------------------------------------------
# OAuth Scopes (PDF-approved)
# ------------------------------------------------------------------
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.send",  # REQUIRED for drafts
]

# ------------------------------------------------------------------
# Internal: build Gmail service
# ------------------------------------------------------------------
def _gmail_service():
    creds = Credentials(
        token=None,
        refresh_token=os.getenv("GMAIL_REFRESH_TOKEN"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=os.getenv("GOOGLE_OAUTH_CLIENT_ID"),
        client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET"),
        scopes=SCOPES,
    )

    return build(
        "gmail",
        "v1",
        credentials=creds,
        cache_discovery=False,
    )

# ------------------------------------------------------------------
# Public API
# ------------------------------------------------------------------

def fetch_unread_messages(max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Fetch unread Gmail messages (metadata + full body).
    NO filtering, NO intelligence here.
    """
    service = _gmail_service()

    try:
        response = service.users().messages().list(
            userId="me",
            q="is:unread",
            maxResults=max_results,
        ).execute()

        messages = []
        for item in response.get("messages", []):
            msg = service.users().messages().get(
                userId="me",
                id=item["id"],
                format="full",
            ).execute()
            messages.append(msg)

        return messages

    except HttpError as e:
        logger.exception("Failed to fetch unread messages: %s", e)
        return []


def search_emails(query: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Search emails in Gmail.
    Used by Email Sender Agent to check last email sent.
    """
    service = _gmail_service()
    
    try:
        response = service.users().messages().list(
            userId="me",
            q=query,
            maxResults=max_results,
        ).execute()
        
        messages = []
        for item in response.get("messages", []):
            # Get full message details
            msg = service.users().messages().get(
                userId="me",
                id=item["id"],
                format="metadata",
                metadataHeaders=["Date", "Subject", "From", "To"]
            ).execute()
            
            # Extract headers
            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            
            messages.append({
                "id": msg["id"],
                "threadId": msg.get("threadId"),
                "date": headers.get("Date"),
                "subject": headers.get("Subject", ""),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "snippet": msg.get("snippet", "")
            })
        
        return messages
        
    except HttpError as e:
        logger.exception("Failed to search emails: %s", e)
        return []


def create_draft(
    to: str,
    subject: str,
    body: str,
    thread_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Create a Gmail draft.
    CRITICAL: This does NOT send email.
    """
    service = _gmail_service()

    raw_message = (
        f"To: {to}\r\n"
        f"Subject: {subject}\r\n"
        f"MIME-Version: 1.0\r\n"
        f"Content-Type: text/plain; charset=utf-8\r\n\r\n"
        f"{body}"
    )

    encoded_message = base64.urlsafe_b64encode(
        raw_message.encode("utf-8")
    ).decode("utf-8")

    draft_body: Dict[str, Any] = {
        "message": {
            "raw": encoded_message,
        }
    }

    if thread_id:
        draft_body["message"]["threadId"] = thread_id

    try:
        draft = service.users().drafts().create(
            userId="me",
            body=draft_body,
        ).execute()

        logger.info("Gmail draft created: %s", draft.get("id"))
        return draft

    except HttpError as e:
        logger.exception("Failed to create Gmail draft: %s", e)
        raise