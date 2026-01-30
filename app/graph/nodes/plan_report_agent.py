from __future__ import annotations
import logging
from datetime import date, datetime
from typing import List, Dict, Any, Optional
from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient

logger = logging.getLogger("presentos.plan_report_agent")

def run_plan_report_node(
    state: PresentOSState,
    notion: NotionClient,
) -> PresentOSState:
    """
    Plan Report Agent (PDF-COMPLIANT, READ-ONLY)
    ROLE:
    - Show user's daily plan
    - Read tasks from POS Tasks DB
    - NEVER mutate data
    - NO XP
    - NO decisions
    """
    if "plan_report_agent" not in state.activated_agents:
        return state

    today = date.today().isoformat()
    tasks_for_today: List[Dict[str, Any]] = []

    try:
        # Get all non-completed tasks
        response = notion._request(
            "POST",
            f"/databases/{notion.db_ids['tasks']}/query",
            json_body={
                "filter": {
                    "and": [
                        {
                            "property": "Status",
                            "select": {"does_not_equal": "Completed"},
                        }
                    ]
                },
                "sorts": [
                    {"property": "Priority", "direction": "ascending"},
                    {"property": "Deadline", "direction": "ascending"},
                ],
                "page_size": 50,
            }
        )
        pages = response.get("results", [])
    except Exception as e:
        logger.exception("Failed to query tasks database")
        state.add_agent_output(
            agent="plan_report_agent",
            result={
                "status": "error", 
                "message": f"Failed to load tasks: {str(e)}"
            },
            score=0.0,
        )
        return state

    for page in pages or []:
        props = page.get("properties", {})

        # Title
        title_items = props.get("Name", {}).get("title", [])
        task_name = title_items[0].get("text", {}).get("content") if title_items else "Untitled Task"

        # Deadline
        deadline_data = props.get("Deadline", {}).get("date", {})
        deadline = deadline_data.get("start") if deadline_data else None
        
        # Filter: include tasks if:
        # 1. No deadline (needs attention) OR
        # 2. Deadline is today OR 
        # 3. Deadline is in the past (overdue)
        include_task = True
        if deadline:
            # Parse deadline date
            try:
                deadline_date = deadline.split("T")[0] if "T" in deadline else deadline
                if deadline_date > today:
                    # Future deadline, skip for today's plan
                    include_task = False
            except:
                # If date parsing fails, include it
                pass
        
        if not include_task:
            continue

        # Optional metadata with safe extraction
        def get_select_value(prop_name: str) -> Optional[str]:
            select_data = props.get(prop_name, {}).get("select", {})
            return select_data.get("name") if select_data else None
        
        def get_relation_name(prop_name: str) -> Optional[str]:
            relation_data = props.get(prop_name, {}).get("relation", [])
            if relation_data:
                # Note: To get the actual name, you'd need to fetch the related page
                # For now, return the relation ID
                return relation_data[0].get("id")
            return None

        tasks_for_today.append({
            "id": page.get("id"),
            "title": task_name,
            "deadline": deadline,
            "priority": get_select_value("Priority"),
            "paei": get_select_value("PAEI"),
            "quest_id": get_relation_name("Quest"),
            "map_id": get_relation_name("Map"),
            "status": get_select_value("Status"),
            "estimated_duration": props.get("Estimated Duration (min)", {}).get("number"),
        })

    # Fetch Calendar Events
    calendar_events = []
    try:
        from app.integrations.google_calendar import list_events
        # Get events starting from now (or beginning of day if needed, but list_events defaults to now)
        # To show full day schedule, we should ideally query from midnight, but let's conform to list_events default or specific usage
        # list_events uses time_min=now by default
        
        # Determine time_min for "today" - start of day
        today_start = f"{today}T00:00:00Z"
        
        events = list_events(max_results=10, time_min=today_start)
        
        for event in events:
            start = event.get("start", {}).get("dateTime") or event.get("start", {}).get("date")
            # Filter for today only
            if start and start.startswith(today):
                calendar_events.append({
                    "id": event.get("id"),
                    "summary": event.get("summary", "No Title"),
                    "start": start,
                    "end": event.get("end", {}).get("dateTime") or event.get("end", {}).get("date"),
                    "location": event.get("location")
                })
    except Exception as e:
        logger.warning(f"Failed to fetch calendar events: {e}")

    # Emit agent output
    state.add_agent_output(
        agent="plan_report_agent",
        result={
            "action": "daily_plan",
            "date": today,
            "tasks": tasks_for_today,
            "calendar_events": calendar_events,
            "summary": {
                "total_tasks": len(tasks_for_today),
                "total_events": len(calendar_events),
                "high_priority": len([t for t in tasks_for_today if t.get("priority") == "High"]),
                "overdue": len([t for t in tasks_for_today if t.get("deadline") and t.get("deadline").split("T")[0] < today]),
            }
        },
        score=0.95 if tasks_for_today or calendar_events else 0.5,
    )

    logger.info("PlanReportAgent completed (%s tasks, %s events)", len(tasks_for_today), len(calendar_events))
    return state