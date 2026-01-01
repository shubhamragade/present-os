"""
Calendar Agent - PDF-COMPLIANT PRODUCTION READY

PDF REQUIREMENTS MET:
- PAEI-aware scheduling (Page 40-41)
- Weather-aware scheduling (Page 14-15)
- Fireflies auto-join (Page 12)
- Energy-based scheduling (Page 10)
- Deep work protection (Page 3)
- Unified coordination (Page 3)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from app.services.calendar_service import parse_iso

from app.graph.state import PresentOSState
from app.services.calendar_service import CalendarService, parse_iso
from app.integrations.notion_client import NotionClient
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.calendar_agent")


def run_calendar_node(
    state: PresentOSState,
    notion: NotionClient,
) -> PresentOSState:
    """
    PDF-COMPLIANT Calendar Agent
    Coordinates with Parent Agent for weather-aware, PAEI-optimized scheduling
    """

    if "calendar_agent" not in state.activated_agents:
        return state

    instruction = get_instruction(state, "calendar_agent")
    if not instruction:
        return state

    intent = instruction.get("intent")
    payload = instruction.get("payload", {})
    paei_context = instruction.get("paei_context", {})
    
    # Extract weather context from Parent Agent (PDF requirement)
    weather_context = payload.get("weather_context", {})
    weather_advisory = payload.get("weather_advisory")
    
    # Build comprehensive user context from PDF requirements
    user_context = {
        "calendar_id": "primary",
        "timezone": state.timezone or "Asia/Kolkata",
        "location": state.meta.get("location", "Santa Monica, CA"),
        "whoop_user_id": state.meta.get("whoop_user_id"),
        "user_id": state.user_id,
        "outdoor_preferences": state.meta.get("outdoor_preferences", ["surf", "hike"]),
        "paei_role": paei_context.get("role", "P"),  # PDF: PAEI-aware scheduling
        "current_energy": state.energy_level or 0.7,
        "whoop_recovery": state.whoop_recovery_score or 70.0,
        "deep_work_blocks": getattr(state.calendar, 'deep_work_blocks', []),
        "today_meetings_count": len(getattr(state.calendar, 'today_events', [])),
        # PDF Weather Context
        "weather_context": weather_context,
        "weather_advisory": weather_advisory,
        "weather_snapshot": state.weather_snapshot
    }

    calendar_service = CalendarService(notion=notion)

    try:
        # PDF-COMPLIANT INTENT HANDLING
        if intent == "schedule_meeting":
            # Add PAEI context to meeting (PDF requirement)
            payload["paei"] = user_context["paei_role"]
            payload["weather_check"] = True  # PDF: Check weather for outdoor
            
            # Apply weather advisory if exists
            if weather_advisory:
                payload["weather_advisory"] = weather_advisory
                if weather_advisory.get("suggestion") == "consider_virtual_meeting":
                    payload["location"] = "Virtual"  # Override outdoor location
            
            # Add Fireflies auto-join flag (PDF requirement)
            payload["auto_transcribe"] = True
            
            result = calendar_service.create_event(payload, user_context)

        elif intent == "block_time_for_activity" or intent == "block_time":
            # Handle perfect surf/kite conditions from Parent Agent
            if weather_context.get("condition_type") == "perfect_kite":
                # PDF: Block time for perfect conditions
                payload["title"] = payload.get("title", "Kitesurf Session (Perfect Conditions)")
                payload["duration_minutes"] = payload.get("duration_minutes", 180)
                payload["priority"] = "high"
                payload["reason"] = "perfect_kite_conditions"
                payload["auto_reschedule_conflicts"] = True
                payload["notify_user"] = True
            
            # Add energy/PAEI context (PDF requirement)
            payload["paei"] = user_context["paei_role"]
            payload["energy_level"] = user_context["current_energy"]
            payload["whoop_recovery"] = user_context["whoop_recovery"]
            
            # Mark as deep work if appropriate (PDF requirement)
            if paei_context.get("role") in ["P", "E"] and payload.get("duration_minutes", 0) >= 60:
                payload["is_deep_work"] = True
                payload["title"] = f"Deep Work: {payload.get('title', 'Task')}"
            
            result = calendar_service.schedule_task(payload, user_context)

        elif intent == "reschedule_event":
            result = calendar_service.reschedule_event(
                event_id=payload.get("event_id"),
                new_start_iso=payload.get("new_start_iso"),
                user_context=user_context,
            )
            
        elif intent == "check_weather_schedule":
            # PDF weather-aware scheduling
            result = calendar_service.find_weather_optimal_slot(payload, user_context)
            
        elif intent == "protect_deep_work":
            # PDF deep work protection
            result = calendar_service.protect_time_block(payload, user_context)
            
        else:
            state.add_agent_output(
                agent="calendar_agent",
                result={
                    "status": "ignored", 
                    "intent": intent,
                    "message": "Unsupported calendar intent"
                },
                score=0.0,
            )
            return state

        # Handle response (support both dict and model)
        if isinstance(result, dict):
            action = result.get("action", "unknown")
            event_data = result.get("event", {})
            confidence = result.get("confidence", 1.0)
            metadata = {k: v for k, v in result.items() 
                       if k not in ["action", "event", "confidence", "success"]}
            success = result.get("success", True)
        else:
            # Handle model response
            action = getattr(result, "action", "unknown")
            event_data = getattr(result, "event", {})
            confidence = getattr(result, "confidence", 1.0)
            metadata = {
                "reasoning": getattr(result, "reasoning", None),
                "task_suggestion": getattr(result, "task_suggestion", None),
                "audit": getattr(result, "audit", [])
            }
            success = getattr(result, "success", True)

        # Extract event ID
        event_id = None
        if isinstance(event_data, dict):
            event_id = event_data.get("id") or event_data.get("eventId") or event_data.get("event_id")
        elif hasattr(event_data, "id"):
            event_id = event_data.id
        elif hasattr(event_data, "event_id"):
            event_id = event_data.event_id
        elif hasattr(event_data, "eventId"):
            event_id = event_data.eventId

        # PDF: Add rich output with all context
        output_result = {
            "action": action,
            "event_id": event_id,
            "confidence": confidence,
            "success": success,
            "paei_optimized": user_context["paei_role"],
            "weather_aware": "weather_context" in user_context and bool(user_context["weather_context"]),
            "energy_aware": "energy_level" in payload,
            "intent": intent,
            **metadata
        }

        # Add Fireflies info if meeting was scheduled
        if action in ["created_event", "scheduled_meeting"] and intent == "schedule_meeting":
            output_result["fireflies_invited"] = True
            output_result["auto_transcription"] = True

        # Add weather info if relevant
        if "weather_score" in result if isinstance(result, dict) else hasattr(result, "weather_score"):
            weather_score = (result.get("weather_score") if isinstance(result, dict) 
                           else getattr(result, "weather_score", 0))
            output_result["weather_score"] = weather_score
            output_result["is_outdoor_friendly"] = weather_score > 0.7
        
        # Add PAEI context to output
        if paei_context:
            output_result["paei_context"] = paei_context

        state.add_agent_output(
            agent="calendar_agent",
            result=output_result,
            score=confidence,
        )

        # PDF: Update state with calendar context for future decisions
        if event_id and action in ["created_event", "scheduled_meeting", "blocked_time", "deep_work_protected"]:
            # Track scheduled events in state
            if "scheduled_events" not in state.meta:
                state.meta["scheduled_events"] = []
            
            new_event = {
                "event_id": event_id,
                "type": "meeting" if intent == "schedule_meeting" else "task_block",
                "paei": user_context["paei_role"],
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "weather_aware": output_result.get("weather_aware", False),
                "intent": intent,
                "action": action
            }
            
            # Add weather context if available
            if weather_context:
                new_event["weather_context"] = weather_context
            
            state.meta["scheduled_events"].append(new_event)
            
            # Keep only last 50 events
            if len(state.meta["scheduled_events"]) > 50:
                state.meta["scheduled_events"] = state.meta["scheduled_events"][-50:]

        return state

    except Exception as e:
        logger.exception("CalendarAgent failed")
        state.add_agent_output(
            agent="calendar_agent",
            result={
                "status": "error", 
                "error": str(e),
                "intent": intent,
                "paei_context": user_context.get("paei_role", "unknown")
            },
            score=0.0,
        )
        return state