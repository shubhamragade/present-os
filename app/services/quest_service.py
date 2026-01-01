# app/services/quest_service.py
"""
Quest Service (SYSTEM OF RECORD WRITER)

Responsibilities:
- Map Quest domain → Notion schema
- Validate structure
- Create Quest pages
- NOTHING else
"""

from __future__ import annotations

from typing import Dict, Any
from datetime import datetime

from app.integrations.notion_client import NotionClient


class QuestService:
    def __init__(self, notion: NotionClient):
        self.notion = notion

    # -------------------------------------------------
    # Create Quest (EXPLICIT)
    # -------------------------------------------------
    def create_quest(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Required:
        - name
        - purpose
        - result
        - category
        - avatar

        Optional:
        - xp_target
        - start_date
        - end_date
        """

        props: Dict[str, Any] = {
            "Name": self.notion._prop_title(data["name"]),
            "Purpose": self.notion._prop_text(data["purpose"]),
            "Result": self.notion._prop_text(data["result"]),
            "Category": self.notion._prop_select(data["category"]),
            "User": self.notion._prop_text(data["avatar"]),
            "Status": self.notion._prop_select("Active"),
        }

        if data.get("xp_target") is not None:
            props["XP Target"] = self.notion._prop_number(
                int(data["xp_target"])
            )

        if data.get("start_date"):
            props["Start Date"] = self.notion._prop_date(data["start_date"])

        if data.get("end_date"):
            props["End Date"] = self.notion._prop_date(data["end_date"])

        body = {
            "parent": {"database_id": self.notion.db_ids["quests"]},
            "properties": props,
        }

        return self.notion._request(
            "POST",
            "/pages",
            json_body=body,
        )
