"""
Fireflies Meeting Agent - Works with YOUR Notion Schema

This agent:
1. Uses your EXACT Notion task schema
2. Integrates with your existing task_agent format
3. Meets all PDF requirements
4. No database changes needed
"""

from __future__ import annotations
import os
import logging
from typing import Dict, Any, List
from datetime import datetime

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.fireflies_agent")


def run_fireflies_node(state: PresentOSState) -> PresentOSState:
    """
    Fireflies agent that creates tasks using YOUR exact Notion schema
    """
    
    instruction = get_instruction(state, "fireflies_agent")
    if not instruction:
        return state
    
    intent = instruction.get("intent")
    payload = instruction.get("payload", {})
    
    try:
        # Initialize Notion client (YOUR existing client)
        notion = NotionClient()
        
        if intent == "process_meeting":
            # PDF: Process meeting and create tasks
            meeting_id = payload.get("meeting_id")
            
            if not meeting_id:
                state.add_agent_output(
                    agent="fireflies_agent",
                    result={
                        "status": "error",
                        "reason": "no_meeting_id"
                    },
                    score=0.0
                )
                return state
            
            # Use the utility function that handles everything
            result = process_fireflies_meeting(
                meeting_id=meeting_id,
                notion_client=notion,
                telegram_token=os.getenv("TELEGRAM_BOT_TOKEN"),
                telegram_chat_id=os.getenv("TELEGRAM_CHAT_ID")
            )
            
            if result.get("success"):
                # Create tasks in Notion using YOUR exact schema
                created_notion_tasks = []
                for task_data in result.get("created_tasks", []):
                    # Build properties exactly like your task_agent.py
                    props = {
                        "Name": notion._prop_title(task_data.get("title", "Meeting Task")),
                        "Status": notion._prop_select("To Do"),
                        "Auto-Scheduled": notion._prop_checkbox(False),
                        "Source": notion._prop_select(task_data.get("source", "Fireflies")),
                    }
                    
                    if task_data.get("description"):
                        props["Description"] = notion._prop_text(task_data["description"])
                    
                    if task_data.get("priority"):
                        props["Priority"] = notion._prop_select(task_data["priority"])
                    
                    if task_data.get("paei"):
                        props["PAEI"] = notion._prop_select(task_data["paei"])
                    
                    # Add Fireflies-specific properties
                    props["Fireflies Meeting"] = notion._prop_checkbox(True)
                    props["Meeting ID"] = notion._prop_text(meeting_id)
                    
                    # Create the task
                    body = {
                        "parent": {"database_id": notion.db_ids["tasks"]},
                        "properties": props,
                    }
                    
                    try:
                        res = notion._request("POST", "/pages", json_body=body)
                        created_notion_tasks.append({
                            "task_id": res.get("id"),
                            "title": task_data.get("title")
                        })
                    except Exception as e:
                        logger.error(f"Failed to create Notion task: {e}")
                
                # Calculate XP (PDF: Awards Integrator XP)
                action_items_count = result.get("tasks_extracted", 0)
                xp_amount = min(max(action_items_count * 5, 10), 50)
                
                # Add XP event to state
                state.planned_actions.append({
                    "type": "xp_event",
                    "paei": "I",  # Integrator XP
                    "reason": f"meeting_coordination_{meeting_id[:8]}",
                    "amount": xp_amount,
                    "source": "fireflies_agent",
                    "meeting_title": result.get("meeting_title")
                })
                
                # Schedule tasks via your calendar system
                for task in created_notion_tasks:
                    state.planned_actions.append({
                        "type": "schedule_task",
                        "task_id": task["task_id"],
                        "description": task["title"],
                        "priority": "Medium",  # Default
                        "estimated_minutes": 30,
                        "source": "fireflies"
                    })
                
                # Success output
                state.add_agent_output(
                    agent="fireflies_agent",
                    result={
                        "action": "meeting_processed",
                        "meeting_id": meeting_id,
                        "meeting_title": result.get("meeting_title"),
                        "tasks_extracted": result.get("tasks_extracted"),
                        "tasks_created": len(created_notion_tasks),
                        "xp_awarded": xp_amount,
                        "telegram_sent": result.get("telegram_sent", False),
                        "created_tasks": created_notion_tasks
                    },
                    score=1.0
                )
                
            else:
                # Error handling
                state.add_agent_output(
                    agent="fireflies_agent",
                    result={
                        "status": "error",
                        "reason": result.get("error", "processing_failed"),
                        "meeting_id": meeting_id
                    },
                    score=0.0
                )
        
        elif intent == "auto_join":
            # Auto-join calendar meeting
            calendar_event = payload.get("calendar_event", {})
            
            try:
                fireflies = FirefliesClient.create_from_env()
                result = fireflies.auto_join_calendar_event(calendar_event)
                
                if result.get("success"):
                    state.add_agent_output(
                        agent="fireflies_agent",
                        result={
                            "action": "meeting_auto_joined",
                            "meeting_id": result.get("meeting_id"),
                            "meeting_title": result.get("meeting_title"),
                            "calendar_event": calendar_event.get("title")
                        },
                        score=1.0
                    )
                    
                    # Schedule transcript processing for after meeting
                    if result.get("meeting_id"):
                        state.planned_actions.append({
                            "type": "process_transcript",
                            "meeting_id": result.get("meeting_id"),
                            "scheduled_time": calendar_event.get("end_time"),
                            "calendar_event": calendar_event
                        })
                else:
                    state.add_agent_output(
                        agent="fireflies_agent",
                        result={
                            "status": "error",
                            "reason": result.get("error", "auto_join_failed"),
                            "calendar_event": calendar_event.get("title")
                        },
                        score=0.0
                    )
                    
            except ValueError as e:
                # Missing API configuration
                state.add_agent_output(
                    agent="fireflies_agent",
                    result={
                        "status": "configuration_error",
                        "error": str(e),
                        "fix": "Set FIREFLIES_API_KEY and FIREFLIES_EMAIL in .env"
                    },
                    score=0.0
                )
        
        else:
            state.add_agent_output(
                agent="fireflies_agent",
                result={
                    "status": "ignored",
                    "reason": "unknown_intent",
                    "intent": intent
                },
                score=0.0
            )
        
        return state
        
    except Exception as e:
        logger.exception("Fireflies agent failed")
        state.add_agent_output(
            agent="fireflies_agent",
            result={
                "status": "error",
                "error": str(e),
                "intent": intent
            },
            score=0.0
        )
        return state