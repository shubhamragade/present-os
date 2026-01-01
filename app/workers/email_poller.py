import time
import logging

from app.integrations.gmail_client import fetch_unread_messages
from app.graph.state import PresentOSState
from app.graph.build_graph import build_presentos_graph

logger = logging.getLogger("presentos.email_poller")


def run_email_poller(interval_seconds: int = 300):
    """
    Poll Gmail every N seconds and process emails
    """
    graph = build_presentos_graph()

    while True:
        try:
            emails = fetch_unread_messages(max_results=5)
            logger.info("Fetched %d unread emails", len(emails))

            for msg in emails:
                state = PresentOSState()
                state.parent_decision = {
                    "instructions": {
                        "email": {
                            "id": msg["id"],
                            "from": _get_header(msg, "From"),
                            "subject": _get_header(msg, "Subject"),
                            "body": _get_body(msg),
                            "received_at": msg.get("internalDate"),
                            "thread_id": msg.get("threadId"),
                        }
                    }
                }
                graph.invoke(state)

        except Exception as e:
            logger.exception("Email poller error: %s", e)

        time.sleep(interval_seconds)


def _get_header(msg, name: str) -> str:
    for h in msg.get("payload", {}).get("headers", []):
        if h["name"].lower() == name.lower():
            return h["value"]
    return ""


def _get_body(msg) -> str:
    parts = msg.get("payload", {}).get("parts", [])
    for p in parts:
        if p.get("mimeType") == "text/plain":
            import base64
            return base64.urlsafe_b64decode(p["body"]["data"]).decode("utf-8")
    return ""
