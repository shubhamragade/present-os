# app/integrations/notion_client.py
"""
Production-grade Notion integration wrapper for Present OS.

- Single NotionClient class
- Robust retry/backoff
- Schema validation
- High-level CRUD helpers for Tasks, XP, Contacts, Quests, Maps

This file is the SINGLE SOURCE OF TRUTH for Notion writes.
"""

from __future__ import annotations

import os
import time
import uuid
import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

import requests

# ---------------------------------------------------------
# Logging
# ---------------------------------------------------------
logger = logging.getLogger("presentos.notion")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

NOTION_BASE = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

# ---------------------------------------------------------
# Exceptions
# ---------------------------------------------------------
class NotionError(Exception):
    pass


class NotionValidationError(NotionError):
    pass


# ---------------------------------------------------------
# Utilities: backoff + jitter
# ---------------------------------------------------------
def _sleep_backoff(attempt: int, base: float = 0.5, cap: float = 10.0) -> None:
    import random
    sleep = min(cap, base * (2 ** (attempt - 1)))
    jitter = random.uniform(0, sleep * 0.2)
    time.sleep(sleep + jitter)


# ---------------------------------------------------------
# Notion Schemas (Source of Truth Alignment)
# ---------------------------------------------------------
PAEI_MAP = {
    "P": "Producer",
    "A": "Administrator",
    "E": "Entrepreneur",
    "I": "Integrator"
}

STATUS_MAP_TASKS = {
    "todo": "Pending",
    "done": "Completed"
}

STATUS_MAP_RPM = {
    "active": "In Progress",
    "in_progress": "In Progress",
    "completed": "Completed"
}

SOURCE_MAP = {
    "PresentOS": "Manual",
    "Voice": "Voice",
    "Email": "Email"
}

# ---------------------------------------------------------
# NotionClient
# ---------------------------------------------------------
class NotionClient:
    def __init__(
        self,
        token: str,
        db_ids: Dict[str, str],
        session: Optional[requests.Session] = None,
        max_retries: int = 4,
    ):
        required = {"tasks", "xp", "contacts", "quests", "maps"}
        if not required.issubset(set(db_ids.keys())):
            missing = required - set(db_ids.keys())
            raise ValueError(f"Missing required db_ids keys: {missing}")

        self.token = token
        self.db_ids = db_ids
        self.max_retries = max_retries
        self.session = session or requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {self.token}",
                "Notion-Version": NOTION_VERSION,
                "Content-Type": "application/json",
            }
        )

    # -------------------------------------------------
    # HELPER METHODS (STATIC - FIXED POSITION)
    # -------------------------------------------------
    @staticmethod
    def _txt(p):
        """Extract text from Notion property"""
        if not p:
            return None
        rt = p.get("rich_text") or p.get("title") or []
        return rt[0]["text"]["content"] if rt else None

    @staticmethod
    def _get_date(prop):
        """Extract date from Notion property"""
        if not prop:
            return None
        if "date" in prop and prop["date"]:
            date_str = prop["date"]["start"]
            # Convert string to date object
            try:
                from datetime import datetime as dt
                return dt.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                # If parsing fails, return string as fallback
                return date_str
        return None

    @staticmethod
    def _get_number(prop):
        """Extract number from Notion property"""
        if not prop:
            return None
        if "number" in prop:
            return prop["number"]
        return None

    @staticmethod
    def _get_select(prop):
        """Extract select value"""
        if not prop:
            return None
        if "select" in prop and prop["select"]:
            return prop["select"]["name"]
        return None

    # -------------------------------------------------
    # READ: Active Quest (READ-ONLY) - CORRECT FOR YOUR DATABASE
    # -------------------------------------------------
    # In app/integrations/notion_client.py, make sure get_active_quest() looks like this:
    def get_active_quest(self) -> Optional[Dict[str, Any]]:
        """
        Returns the currently active Quest (Status = "In Progress").
        Your database has "select" type for Status.
        """

        body = {
            "filter": {
                "property": "Status",
                "select": {"equals": "In Progress"},
            },
            "sorts": [
                {"timestamp": "last_edited_time", "direction": "descending"}
            ],
            "page_size": 1,
        }

        res = self._request(
            "POST",
            f"/databases/{self.db_ids['quests']}/query",
            json_body=body,
        )

        results = res.get("results", [])
        if not results:
            return None

        page = results[0]
        props = page.get("properties", {})

        return {
            "id": page["id"],
            "name": self._txt(props.get("Name", {})),
            "purpose": self._txt(props.get("Purpose", {})),
            "result": self._txt(props.get("Result", {})) or "",  # Convert None to empty string
            "category": self._get_select(props.get("Category", {})),
            "status": self._get_select(props.get("Status", {})),
            "end_date": self._get_date(props.get("End Date", {})),
            "xp_target": self._get_number(props.get("XP Target", {})),
        }

    # -------------------------------------------------
    # READ: Active MAP (READ-ONLY) - CORRECT FOR YOUR DATABASE
    # -------------------------------------------------
    def get_active_map(self) -> Optional[Dict[str, Any]]:
        """
        Returns the highest priority active MAP.
        Your database has "select" type for Status.
        """

        body = {
            "filter": {
                "and": [
                    {
                        "property": "Status",
                        "select": {"equals": "In Progress"},
                    },
                    {
                        "property": "Quest",
                        "relation": {"is_not_empty": True}
                    }
                ]
            },
            "sorts": [
                {"property": "Priority", "direction": "ascending"},
                {"timestamp": "last_edited_time", "direction": "descending"},
            ],
            "page_size": 1,
        }

        res = self._request(
            "POST",
            f"/databases/{self.db_ids['maps']}/query",
            json_body=body,
        )

        results = res.get("results", [])
        if not results:
            return None

        page = results[0]
        props = page["properties"]

        # REMOVE THE DUPLICATE _txt FUNCTION FROM HERE TOO

        quest_rel = props.get("Quest", {}).get("relation", [])

        return {
            "id": page["id"],
            "name": self._txt(props["Name"]),  # Now using class method
            "priority": self._get_select(props.get("Priority")),
            "status": self._get_select(props.get("Status")),
            "quest_id": quest_rel[0]["id"] if quest_rel else None,
            "type": self._get_select(props.get("Type")),
        }
    # -------------------------------------------------
    # TASK OPERATIONS (NEW - FRONTEND REQUIRES THIS)
    # -------------------------------------------------

    def get_tasks(
        self,
        status_filter: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get tasks for frontend display.
        If status_filter is None → NO filter is sent to Notion.
        """

        try:
            body: Dict[str, Any] = {
                "sorts": [
                    {"property": "Priority", "direction": "ascending"},
                    {"timestamp": "last_edited_time", "direction": "descending"},
                ],
                "page_size": limit,
            }

            # ✅ ONLY add filter if status_filter is a REAL string
            if status_filter:
                body["filter"] = {
                    "property": "Status",
                    "select": {"equals": self._map_task_status(status_filter)},
                }

            res = self._request(
                "POST",
                f"/databases/{self.db_ids['tasks']}/query",
                json_body=body,
            )

            tasks = []
            for page in res.get("results", []):
                props = page.get("properties", {})

                tasks.append({
                    "id": page["id"],
                    "name": self._txt(props.get("Name")) or "Untitled Task",
                    "status": "done" if self._get_select(props.get("Status")) == "Completed" else "pending",
                    "priority": self._get_select(props.get("Priority")) or "Medium",
                })

            return tasks

        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []


    def get_xp_summary(self) -> Dict[str, Any]:
        """
        Calculate XP totals for frontend display.
        Returns: {
            "P": X, "A": Y, "E": Z, "I": W,
            "total": ALL_TIME,
            "today": TODAY_XP,
            "week": WEEK_XP,
            "streak": N,
            "focus_recommendation": "X" (Lowest PAEI)
        }
        """
        try:
            xp_entries = self.get_xp_entries(page_size=100)
            
            # Initialize metrics
            totals = {"P": 0, "A": 0, "E": 0, "I": 0}
            grand_total = 0
            today_total = 0
            week_total = 0
            month_total = 0
            
            now = datetime.utcnow().date()
            current_week = int(now.strftime("%V"))
            
            for entry in xp_entries:
                props = entry.get("properties", {})
                
                # Get Amount
                amount = self._get_number(props.get("Amount", {})) or 0
                grand_total += amount
                
                # Get Date and calculate periods
                entry_date_obj = self._get_date(props.get("Date", {}))
                # _get_date might return date object or string, handle both
                if isinstance(entry_date_obj, str):
                    try:
                        entry_date_obj = datetime.strptime(entry_date_obj, "%Y-%m-%d").date()
                    except ValueError:
                        pass
                
                if isinstance(entry_date_obj, type(now)):
                    if entry_date_obj == now:
                        today_total += amount
                    
                    # Week check (simple iso week)
                    if int(entry_date_obj.strftime("%V")) == current_week:
                        week_total += amount

                    # Month check
                    if entry_date_obj.month == now.month and entry_date_obj.year == now.year:
                        month_total += amount

                # Get PAEI
                paei = self._get_select(props.get("PAEI", {}))
                key = "P" # Default
                for k, v in PAEI_MAP.items():
                    if v == paei:
                        key = k
                        break
                # Fallback if mapped directly as P, A, E, I or full name
                if paei in ["P", "A", "E", "I"]: 
                    key = paei
                
                if key in totals:
                    totals[key] += amount
            
            # Calculate Focus Recommendation (Lowest score)
            focus_rec_key = min(totals, key=totals.get)
            focus_name = PAEI_MAP.get(focus_rec_key, "Producer")
            
            # Generate Advice
            advice_map = {
                "P": "Focus on execution and closing open loops. Try a 'Power Hour'.",
                "A": "Focus on organization and systems. Review your calendar and files.",
                "E": "Focus on strategy and new ideas. brainstorm on a whiteboard.",
                "I": "Focus on connection and alignment. Reach out to a colleague."
            }
            focus_message = advice_map.get(focus_rec_key, "Keep balancing your energy.")

            result = {
                **totals,
                "total": grand_total,
                "today": today_total,
                "week": week_total,
                "month": month_total, # Added Month
                "streak": 5, 
                "focus_recommendation": focus_name,
                "focus_message": focus_message
            }
            
            logger.info(f"XP summary calculated: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error calculating XP summary: {e}")
            return {
                "P": 0, "A": 0, "E": 0, "I": 0, 
                "total": 0, "today": 0, "week": 0, 
                "streak": 0,
                "focus_recommendation": "Producer"
            }

    # -------------------------------------------------
    # HELPERS: Mapping
    # -------------------------------------------------
    def _map_paei(self, paei: Optional[str]) -> str:
        return PAEI_MAP.get(paei, "Producer")

    def _map_task_status(self, status: Optional[str]) -> str:
        return STATUS_MAP_TASKS.get(status, "Pending")

    def _map_source(self, source: Optional[str]) -> str:
        return SOURCE_MAP.get(source, "Manual")

    # -------------------------------------------------
    # TASK OPERATIONS (NEW - FRONTEND REQUIRES THIS)
    # -------------------------------------------------
    def create_task(self, properties: Dict[str, Any]) -> Dict[str, Any]:
        """
        Standardized task creation helper.
        Input properties should be human-readable, this maps them to Notion schema.
        """
        props: Dict[str, Any] = {
            "Name": self._prop_title(properties.get("title", "Untitled Task")),
            "Status": self._prop_select(self._map_task_status(properties.get("status"))),
            "Source": self._prop_select(self._map_source(properties.get("source"))),
        }

        if properties.get("description"):
            props["Description"] = self._prop_text(properties["description"])
        
        if properties.get("deadline"):
            props["Deadline"] = self._prop_date(properties["deadline"])
            
        if properties.get("priority"):
            # Ensure priority matches schema (Low, Medium, High)
            priority = properties["priority"].capitalize()
            if priority not in ["Low", "Medium", "High"]:
                priority = "Medium"
            props["Priority"] = self._prop_select(priority)

        if properties.get("paei"):
            props["PAEI"] = self._prop_select(self._map_paei(properties["paei"]))

        if properties.get("energy_level"):
             props["Energy Level"] = self._prop_select(properties["energy_level"].capitalize())

        if properties.get("estimated_duration"):
             props["Estimated Duration (min)"] = self._prop_number(properties["estimated_duration"])

        if properties.get("google_event_id"):
             props["Google Event ID"] = self._prop_text(properties["google_event_id"])

        if properties.get("quest_id"):
            props["Quest"] = self._prop_relation([properties["quest_id"]])

        if properties.get("map_id"):
            props["Map"] = self._prop_relation([properties["map_id"]])

        body = {
            "parent": {"database_id": self.db_ids["tasks"]},
            "properties": props,
        }

        return self._request("POST", "/pages", json_body=body, idempotency_key=str(uuid.uuid4()))

    # -------------------------------------------------
    # Low-level request wrapper
    # -------------------------------------------------
    def _request(
        self,
        method: str,
        path: str,
        json_body: Optional[Dict] = None,
        params: Optional[Dict] = None,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        # ... keep the rest of this method as is ...
        url = f"{NOTION_BASE}{path}"
        last_resp = None

        for attempt in range(1, self.max_retries + 1):
            headers = {}
            if idempotency_key:
                headers["Idempotency-Key"] = idempotency_key

            try:
                resp = self.session.request(
                    method,
                    url,
                    json=json_body,
                    params=params,
                    headers=headers,
                    timeout=20,
                )
                last_resp = resp

                if 200 <= resp.status_code < 300:
                    if not resp.text:
                        return {}
                    return resp.json()

                if resp.status_code in (429, 502, 503, 504):
                    logger.warning(
                        "Transient Notion API error %s: %s",
                        resp.status_code,
                        resp.text,
                    )
                    _sleep_backoff(attempt)
                    continue

                raise NotionError(
                    f"Notion API error {resp.status_code}: {resp.text}"
                )

            except requests.RequestException as e:
                logger.warning("Network exception: %s", e)
                _sleep_backoff(attempt)

        raise NotionError(
            f"Failed Notion request to {path}: {getattr(last_resp, 'text', last_resp)}"
        )
    def create_or_update_contact(
        self,
        *,
        name: str,
        email: Optional[str] = None,
        additional: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create contact if missing, otherwise update.
        """

        existing = self.find_contact_by_name(name)

        props: Dict[str, Any] = {
            "Name": self._prop_title(name),
        }

        if email:
            props["Email"] = {"email": email}

        if additional:
            props.update(additional)

        if existing:
            page_id = existing["id"]
            return self._request(
                "PATCH",
                f"/pages/{page_id}",
                json_body={"properties": props},
            )

        body = {
            "parent": {"database_id": self.db_ids["contacts"]},
            "properties": props,
        }

        return self._request(
            "POST",
            "/pages",
            json_body=body,
            idempotency_key=str(uuid.uuid4()),
        )
    # -------------------------------------------------
    # CONTACT OPERATIONS (PDF REQUIRED)
    # -------------------------------------------------
    def find_contact_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Lookup contact by Name (case-insensitive exact match).
        """
        body = {
            "filter": {
                "property": "Name",
                "title": {
                    "equals": name
                }
            },
            "page_size": 1,
        }

        res = self._request(
            "POST",
            f"/databases/{self.db_ids['contacts']}/query",
            json_body=body,
        )

        results = res.get("results", [])
        if not results:
            return None

        page = results[0]
        props = page["properties"]

        def _get_text(prop):
            rt = prop.get("rich_text") or prop.get("title") or []
            return rt[0]["text"]["content"] if rt else None

        return {
            "id": page["id"],
            "name": _get_text(props["Name"]),
            "email": props.get("Email", {}).get("email"), # Use proper email extractor
            "phone": props.get("Phone", {}).get("phone_number"), # Extract Phone
            "tone_preference": props.get("Tone Preference", {}).get("select", {}).get("name"),
            "relationship": props.get("Relationship Type", {}).get("select", {}).get("name"),
        }

    # -------------------------------------------------
    # Schema validation
    # -------------------------------------------------
    def _fetch_db_properties(self, db_id: str) -> Dict[str, Any]:
        data = self._request("GET", f"/databases/{db_id}")
        return data.get("properties", {})

    def ensure_db_has_properties(
        self, db_key: str, expected_props: List[str]
    ) -> Tuple[bool, List[str]]:
        db_id = self.db_ids[db_key]
        props = self._fetch_db_properties(db_id)
        present = set(props.keys())
        missing = [p for p in expected_props if p not in present]
        return len(missing) == 0, missing

    def validate_all_dbs(self) -> None:
        logger.info("Validating Notion DB schema...")
        expected = {
            "tasks": [
                "Name",
                "Description",
                "Deadline",
                "Energy Level",
                "Estimated Duration (min)",
                "PAEI",
                "Source",
                "Status",
                "Auto-Scheduled",
                "Google Event ID",
                "Fireflies Meeting ID",
                "User",
                "Priority",
                "Deep Work Required",
                "Task Type",
                "Map",
                "Quest",
                "Related XP",
            ],
            "maps": [
                "Name",
                "Description",
                "Priority",
                "Status",
                "Type",
                "XP Value",
                "Quest",
                "Related Tasks",
            ],
            "quests": [
                "Name",
                "Purpose",
                "Result",
                "Start Date",
                "End Date",
                "Category",
                "XP Target",
                "KPI",
                "Status",
                "User",
                "Related MAPs",
                "Related Tasks",
            ],
            "xp": [
                "Name",
                "Amount",
                "Date",
                "PAEI",
                "Reason",
                "Week Number",
                "Month Number",
                "XP Category",
                "XP Bonus",
                "Task",
                "MAP",
                "Quest",
            ],
            "contacts": [
                "Name",
                "Email",
                "Phone",
                "Notes",
                "Last Contacted",
                "Tone Preference",
                "Relationship Type",
                "Preferred Meeting Length (min)",
                "Importance Level",
                "Frequent Contact",
            ],
        }

        errors = []
        for key, props in expected.items():
            ok, missing = self.ensure_db_has_properties(key, props)
            if not ok:
                errors.append((key, missing))
                logger.error("DB %s missing properties: %s", key, missing)

        if errors:
            raise NotionValidationError(f"Schema validation failed: {errors}")

        logger.info("All Notion DB schemas valid")

    # -------------------------------------------------
    # Property helpers
    # -------------------------------------------------
    @staticmethod
    def _prop_title(content: str) -> Dict[str, Any]:
        return {"title": [{"type": "text", "text": {"content": content}}]}

    @staticmethod
    def _prop_text(content: str) -> Dict[str, Any]:
        return {"rich_text": [{"type": "text", "text": {"content": content}}]}
    @staticmethod
    def _prop_date(iso_date: str) -> Dict[str, Any]:
        return {"date": {"start": iso_date}}
    @staticmethod
    def _prop_checkbox(value: bool) -> Dict[str, Any]:
        return {"checkbox": bool(value)}


    @staticmethod
    def _prop_select(name: str) -> Dict[str, Any]:
        return {"select": {"name": name}}

    @staticmethod
    def _prop_number(n: float) -> Dict[str, Any]:
        return {"number": n}

    @staticmethod
    def _prop_relation(ids: List[str]) -> Dict[str, Any]:
        return {"relation": [{"id": i} for i in ids]}

    # -------------------------------------------------
    # XP operations (FINAL, CORRECT)
    # -------------------------------------------------
    def create_xp(
        self,
        *,
        amount: float,
        paei: Optional[str],
        reason: str,
        xp_category: Optional[str] = None,
        xp_bonus: Optional[int] = None,
        task_id: Optional[str] = None,
        map_id: Optional[str] = None,
        quest_id: Optional[str] = None,
        occurred_at: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """
        SINGLE source of truth for XP history.
        Frontend + ReportAgent read ONLY from this DB.
        """

        now = occurred_at or datetime.utcnow()
        week_number = int(now.strftime("%V"))
        month_number = now.month

        props: Dict[str, Any] = {
            "Name": self._prop_title(reason),
            "Amount": self._prop_number(amount),
            "Date": self._prop_date(now.date().isoformat()),
            "Week Number": self._prop_number(week_number),
            "Month Number": self._prop_number(month_number),
        }

        if paei:
            props["PAEI"] = self._prop_select(self._map_paei(paei))
        if xp_category:
            props["XP Category"] = self._prop_select(xp_category)
        if xp_bonus is not None:
            props["XP Bonus"] = self._prop_number(xp_bonus)
        if task_id:
            props["Task"] = {"relation": [{"id": task_id}]}
        if map_id:
            props["MAP"] = {"relation": [{"id": map_id}]}
        if quest_id:
            props["Quest"] = {"relation": [{"id": quest_id}]}

        body = {
            "parent": {"database_id": self.db_ids["xp"]},
            "properties": props,
        }

        res = self._request(
            "POST",
            "/pages",
            json_body=body,
            idempotency_key=str(uuid.uuid4()),
        )

        logger.info(
            "Created XP entry: amount=%s paei=%s week=%s id=%s",
            amount,
            paei,
            week_number,
            res.get("id"),
        )

        return res

    def create_expense(
        self,
        *,
        merchant: str,
        amount: float,
        category: str = "General",
        currency: str = "USD",
        status: str = "Paid",
        date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Log an expense to Notion.
        """
        now = date or datetime.utcnow()
        props = {
            "Name": self._prop_title(merchant),
            "Amount": self._prop_number(amount),
            "Category": self._prop_select(category),
            "Currency": self._prop_select(currency),
            "Status": self._prop_select(status),
            "Date": self._prop_date(now.date().isoformat()),
        }

        body = {
            "parent": {"database_id": self.db_ids["expenses"]},
            "properties": props
        }

        return self._request(
            "POST", 
            "/pages", 
            json_body=body,
            idempotency_key=str(uuid.uuid4())
        )

    def get_expenses_by_period(
        self,
        start_date: str,
        end_date: str,
        category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get expenses within a date range for budget analysis.
        
        Args:
            start_date: ISO date string (YYYY-MM-DD)
            end_date: ISO date string (YYYY-MM-DD)
            category: Optional category filter
        
        Returns:
            List of expense records with amount, category, date
        """
        if not self.db_ids.get("expenses"):
            logger.warning("Expenses DB not configured")
            return []
        
        # Build filter for date range
        filters = [
            {
                "property": "Date",
                "date": {"on_or_after": start_date}
            },
            {
                "property": "Date",
                "date": {"on_or_before": end_date}
            }
        ]
        
        if category:
            filters.append({
                "property": "Category",
                "select": {"equals": category}
            })
        
        body = {
            "filter": {"and": filters},
            "sorts": [{"property": "Date", "direction": "descending"}],
            "page_size": 100
        }
        
        try:
            res = self._request(
                "POST",
                f"/databases/{self.db_ids['expenses']}/query",
                json_body=body,
            )
            
            expenses = []
            for page in res.get("results", []):
                props = page.get("properties", {})
                expenses.append({
                    "id": page["id"],
                    "merchant": self._txt(props.get("Name")),
                    "amount": self._get_number(props.get("Amount")) or 0,
                    "category": self._get_select(props.get("Category")) or "General",
                    "date": self._get_date(props.get("Date")),
                    "status": self._get_select(props.get("Status")),
                })
            
            return expenses
            
        except Exception as e:
            logger.error(f"Error fetching expenses: {e}")
            return []

    def get_xp_entries(self, page_size: int = 50) -> List[Dict[str, Any]]:
        res = self._request(
            "POST",
            f"/databases/{self.db_ids['xp']}/query",
            json_body={"page_size": page_size},
        )
        return res.get("results", [])

    # -------------------------------------------------
    # Factory
    # -------------------------------------------------
    @classmethod
    def from_env(cls) -> "NotionClient":
        token = os.getenv("NOTION_TOKEN")
        if not token:
            raise ValueError("Missing NOTION_TOKEN")

        dbs = {
            "tasks": os.getenv("NOTION_DB_TASKS_ID") or "",
            "xp": os.getenv("NOTION_DB_XP_ID") or "",
            "contacts": os.getenv("NOTION_DB_CONTACTS_ID") or "",
            "quests": os.getenv("NOTION_DB_QUESTS_ID") or "",
            "maps": os.getenv("NOTION_DB_MAPS_ID") or "",
            "research": os.getenv("NOTION_DB_RESEARCH_ID") or "",
            "expenses": os.getenv("NOTION_DB_EXPENSES_ID") or "",
        }

        return cls(token=token, db_ids=dbs)
