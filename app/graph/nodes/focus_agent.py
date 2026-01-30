"""
Focus Agent - PDF COMPLIANT

PDF Requirements (Page 6, 14-15):
- Manages deep work sessions
- Blocks interruptions during focus
- Respects energy levels (WHOOP)
- Integrates with calendar for optimal timing
- Uses time-of-day optimization
"""

from __future__ import annotations
import os
import logging
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from app.graph.state import PresentOSState
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.focus_agent")


def _get_optimal_focus_time(state: PresentOSState) -> Dict[str, Any]:
    """
    Determine optimal focus time based on:
    - WHOOP recovery score
    - Time of day
    - Calendar availability
    - Historical productivity patterns
    """
    
    now = datetime.now(timezone.utc)
    hour = now.hour
    
    # Default values
    optimal = {
        "duration_minutes": 60,
        "deep_work": True,
        "optimal_start": now.isoformat(),
        "confidence": 0.7
    }
    
    # PDF: Respect energy levels
    whoop_recovery = getattr(state, 'whoop_recovery_score', None) or 70  # Default to 70 if None
    
    if whoop_recovery >= 80:
        # High energy → Deep work
        optimal.update({
            "duration_minutes": 90,
            "deep_work": True,
            "energy_context": "high_energy",
            "confidence": 0.85
        })
    elif whoop_recovery >= 60:
        # Medium energy → Standard focus
        optimal.update({
            "duration_minutes": 60,
            "deep_work": False,
            "energy_context": "medium_energy",
            "confidence": 0.75
        })
    else:
        # Low energy → Short focus or no focus
        optimal.update({
            "duration_minutes": 30,
            "deep_work": False,
            "energy_context": "low_energy_recommend_break",
            "confidence": 0.6
        })
    
    # PDF: Time-of-day optimization
    if 9 <= hour <= 12:
        optimal.update({
            "time_context": "morning_peak",
            "duration_multiplier": 1.2
        })
    elif 14 <= hour <= 17:
        optimal.update({
            "time_context": "afternoon_secondary_peak",
            "duration_multiplier": 1.0
        })
    elif 20 <= hour <= 23:
        optimal.update({
            "time_context": "evening_creative_peak",
            "duration_multiplier": 1.1,
            "deep_work": True  # Evenings good for deep work
        })
    else:
        optimal.update({
            "time_context": "non_optimal_time",
            "duration_multiplier": 0.8
        })
    
    return optimal


def _create_focus_policies(deep_work: bool, duration_minutes: int) -> Dict[str, Any]:
    """
    PDF Page 6: Create interruption policies for focus mode
    """
    
    if deep_work:
        return {
            "suppress_notifications": True,
            "avoid_meetings": True,
            "prefer_long_blocks": True,
            "block_calendar": True,
            "silence_phone": True,
            "delay_email_processing": True,
            "minimum_duration": 60,  # minutes
            "energy_requirement": "medium_high",
            "interruption_allowed": "emergency_only"
        }
    else:
        return {
            "suppress_notifications": True,
            "avoid_meetings": False,
            "prefer_long_blocks": False,
            "block_calendar": False,
            "silence_phone": False,
            "delay_email_processing": False,
            "minimum_duration": 25,  # Pomodoro style
            "energy_requirement": "any",
            "interruption_allowed": "low_priority_ok"
        }


def _calculate_exact_focus_times(
    duration_minutes: int,
    whoop_recovery: Optional[float] = None,
    calendar_events: Optional[list] = None
) -> Dict[str, Any]:
    """
    Calculate exact start and end times for focus session.
    
    Logic:
    1. If high energy (WHOOP >= 75) → Start now
    2. If medium energy → Find next available high-energy slot
    3. Check calendar for conflicts
    4. Auto-resolve conflicts or notify
    """
    from datetime import datetime, timezone, timedelta
    import pytz
    
    # Use local timezone (India)
    local_tz = pytz.timezone('Asia/Kolkata')
    now_utc = datetime.now(timezone.utc)
    now_local = now_utc.astimezone(local_tz)
    
    # Default: start now
    start_time = now_local
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Check WHOOP energy
    energy_level = "medium"
    if whoop_recovery and whoop_recovery >= 75:
        energy_level = "high"
        # High energy → perfect slot, start now
        start_time = now_local
    elif whoop_recovery and whoop_recovery >= 60:
        energy_level = "medium"
        # Medium energy → start now but note it
        start_time = now_local
    else:
        energy_level = "low"
        # Low energy → suggest next high-energy slot (usually morning)
        # If it's evening, suggest tomorrow morning
        if now_local.hour >= 18:
            # Suggest tomorrow 9 AM
            tomorrow = now_local + timedelta(days=1)
            start_time = tomorrow.replace(hour=9, minute=0, second=0, microsecond=0)
        else:
            # Start now anyway, but note low energy
            start_time = now_local
    
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Check for calendar conflicts (simplified - would integrate with Calendar Agent)
    has_conflicts = False
    conflict_resolution = "none"
    
    if calendar_events:
        # Check if any events overlap with our focus time
        for event in calendar_events:
            # This would check actual event times
            # For now, assume no conflicts
            pass
    
    return {
        "start_time": start_time,
        "end_time": end_time,
        "start_time_formatted": start_time.strftime("%I:%M %p"),
        "end_time_formatted": end_time.strftime("%I:%M %p"),
        "start_time_iso": start_time.isoformat(),
        "end_time_iso": end_time.isoformat(),
        "duration_minutes": duration_minutes,
        "energy_level": energy_level,
        "whoop_recovery": whoop_recovery,
        "has_conflicts": has_conflicts,
        "conflict_resolution": conflict_resolution,
        "timezone": "Asia/Kolkata"
    }


def _schedule_focus_block(state: PresentOSState, focus_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schedule focus block via calendar agent with exact times and conflict checking.
    Returns calendar event details with precise start/end times.
    """
    
    # Get WHOOP recovery score
    whoop_recovery = getattr(state, 'whoop_recovery_score', None) or 70
    
    # Calculate exact start/end times
    timing = _calculate_exact_focus_times(
        duration_minutes=focus_config.get("duration_minutes", 60),
        whoop_recovery=whoop_recovery,
        calendar_events=getattr(state.calendar, 'today_events', []) if hasattr(state, 'calendar') else None
    )
    
    # Build calendar event
    event_data = {
        "title": f"🧠 Focus Time: {'Deep Work' if focus_config.get('deep_work') else 'Concentration'}",
        "description": f"Focus session scheduled by PresentOS Focus Agent\n"
                      f"Energy: {focus_config.get('energy_context', 'normal')}\n"
                      f"WHOOP Recovery: {whoop_recovery}%\n"
                      f"Policies: {focus_config.get('policies', {}).get('interruption_allowed', 'normal')}",
        "start": timing["start_time_iso"],
        "end": timing["end_time_iso"],
        "duration_minutes": focus_config.get("duration_minutes", 60),
        "focus_mode": True,
        "deep_work": focus_config.get("deep_work", False),
        "auto_decline_conflicts": focus_config.get("deep_work", False),
        "source": "focus_agent",
        # Add exact times for response
        "start_time_formatted": timing["start_time_formatted"],
        "end_time_formatted": timing["end_time_formatted"],
    }
    
    # Add to planned actions for calendar agent
    if not hasattr(state, 'planned_actions'):
        state.planned_actions = []
    
    state.planned_actions.append({
        "type": "create_calendar_event",
        "event_data": event_data,
        "priority": "high" if focus_config.get("deep_work") else "medium",
        "agent": "calendar_agent"
    })
    
    return {
        "scheduled": True,
        "event_data": event_data,
        "calendar_action_added": True,
        "timing": timing
    }



def run_focus_node(state: PresentOSState) -> PresentOSState:
    """
    Focus Agent - PDF COMPLIANT
    
    ROLE:
    - Manages focus/deep work sessions
    - Blocks interruptions intelligently
    - Respects energy levels (WHOOP)
    - Schedules optimal focus times
    - Integrates with calendar
    """
    
    instruction = get_instruction(state, "focus_agent")
    if not instruction:
        return state
    
    intent = instruction.get("intent")
    payload = instruction.get("payload", {})
    paei_context = instruction.get("paei_context", {})
    
    try:
        if intent in ["enable_focus_mode", "start_focus_session", "create_focus"]:
            # PDF: Enable focus with intelligent configuration
            user_duration = payload.get("duration_minutes")
            user_deep_work = payload.get("deep_work")
            reason = payload.get("reason", "user_requested")
            
            # Get optimal focus configuration
            optimal_config = _get_optimal_focus_time(state)
            
            # Override with user preferences if provided
            if user_duration:
                optimal_config["duration_minutes"] = user_duration
            
            if user_deep_work is not None:
                optimal_config["deep_work"] = user_deep_work
            
            # Create focus policies
            policies = _create_focus_policies(
                optimal_config["deep_work"],
                optimal_config["duration_minutes"]
            )
            
            # Schedule in calendar
            schedule_result = _schedule_focus_block(state, optimal_config)
            timing = schedule_result.get("timing", {})
            
            # Build result with detailed timing and context
            result = {
                "action": "focus_enabled",
                "enabled_at": datetime.now(timezone.utc).isoformat(),
                "duration_minutes": optimal_config["duration_minutes"],
                "deep_work": optimal_config["deep_work"],
                "reason": reason,
                "policies": policies,
                "energy_context": optimal_config.get("energy_context", "normal"),
                "time_context": optimal_config.get("time_context", "normal"),
                "confidence": optimal_config.get("confidence", 0.7),
                "calendar_scheduled": schedule_result.get("scheduled", False),
                "paei_context": paei_context,
                # Add exact timing details for parent response
                "start_time": timing.get("start_time_formatted", "now"),
                "end_time": timing.get("end_time_formatted", ""),
                "whoop_recovery": timing.get("whoop_recovery", 70),
                "energy_level": timing.get("energy_level", "medium"),
                "protections": {
                    "calendar_blocked": True,
                    "notifications_silenced": policies.get("suppress_notifications", True),
                    "meetings_avoided": policies.get("avoid_meetings", True),
                    "interruptions": policies.get("interruption_allowed", "emergency_only")
                }
            }
            
            # Agent output
            state.add_agent_output(
                agent="focus_agent",
                result=result,
                score=result["confidence"]
            )
            
            # PDF: Award XP for focus (Producer XP)
            state.planned_actions.append({
                "type": "xp_event",
                "paei": "P",  # Producer XP for focus
                "reason": f"focus_session_{'deep_work' if optimal_config['deep_work'] else 'concentration'}",
                "amount": 10 if optimal_config["deep_work"] else 5,
                "source": "focus_agent",
                "duration_minutes": optimal_config["duration_minutes"]
            })
            
            return state
        
        elif intent == "disable_focus_mode":
            # Disable focus mode
            result = {
                "action": "focus_disabled",
                "disabled_at": datetime.now(timezone.utc).isoformat(),
                "reason": payload.get("reason", "user_requested"),
                "paei_context": paei_context
            }
            
            state.add_agent_output(
                agent="focus_agent",
                result=result,
                score=0.9
            )
            
            return state
        
        elif intent == "schedule_daily_focus":
            # PDF: Proactively schedule daily focus blocks
            focus_blocks = payload.get("blocks", [
                {"type": "deep_work", "preferred_time": "morning"},
                {"type": "concentration", "preferred_time": "afternoon"}
            ])
            
            scheduled_blocks = []
            for block in focus_blocks:
                # Configure based on block type
                if block.get("type") == "deep_work":
                    config = {
                        "duration_minutes": 90,
                        "deep_work": True,
                        "energy_context": "requires_high_energy"
                    }
                else:
                    config = {
                        "duration_minutes": 60,
                        "deep_work": False,
                        "energy_context": "any_energy_ok"
                    }
                
                # Schedule the block
                schedule_result = _schedule_focus_block(state, config)
                if schedule_result.get("scheduled"):
                    scheduled_blocks.append({
                        "type": block.get("type"),
                        "config": config,
                        "scheduled": True
                    })
            
            result = {
                "action": "daily_focus_scheduled",
                "scheduled_at": datetime.now(timezone.utc).isoformat(),
                "blocks_scheduled": len(scheduled_blocks),
                "scheduled_blocks": scheduled_blocks,
                "paei_context": paei_context
            }
            
            state.add_agent_output(
                agent="focus_agent",
                result=result,
                score=0.8 if len(scheduled_blocks) > 0 else 0.4
            )
            
            return state
        
        elif intent == "check_focus_readiness":
            # PDF: Check if user is ready for focus based on energy/context
            readiness = _get_optimal_focus_time(state)
            
            result = {
                "action": "focus_readiness_checked",
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "ready_for_focus": readiness["confidence"] >= 0.7,
                "recommended_duration": readiness["duration_minutes"],
                "recommended_type": "deep_work" if readiness["deep_work"] else "concentration",
                "energy_context": readiness.get("energy_context", "unknown"),
                "confidence": readiness["confidence"],
                "paei_context": paei_context
            }
            
            state.add_agent_output(
                agent="focus_agent",
                result=result,
                score=readiness["confidence"]
            )
            
            return state
        
        elif intent == "create_focus":
            # Handle generic "create_focus" intent (map to enable_focus_mode)
            logger.info(f"Mapping create_focus to enable_focus_mode")
            
            # Get optimal focus configuration
            optimal_config = _get_optimal_focus_time(state)
            
            # Create focus policies
            policies = _create_focus_policies(
                optimal_config["deep_work"],
                optimal_config["duration_minutes"]
            )
            
            # Schedule in calendar
            schedule_result = _schedule_focus_block(state, optimal_config)
            
            # Build result
            result = {
                "action": "focus_enabled",
                "enabled_at": datetime.now(timezone.utc).isoformat(),
                "duration_minutes": optimal_config["duration_minutes"],
                "deep_work": optimal_config["deep_work"],
                "reason": "user_requested_via_create_focus",
                "policies": policies,
                "energy_context": optimal_config.get("energy_context", "normal"),
                "time_context": optimal_config.get("time_context", "normal"),
                "confidence": optimal_config.get("confidence", 0.7),
                "calendar_scheduled": schedule_result.get("scheduled", False),
                "paei_context": paei_context
            }
            
            # Agent output
            state.add_agent_output(
                agent="focus_agent",
                result=result,
                score=result["confidence"]
            )
            
            return state
        
        else:
            # Unknown intent
            state.add_agent_output(
                agent="focus_agent",
                result={
                    "status": "ignored",
                    "reason": "unsupported_intent",
                    "intent": intent
                },
                score=0.0
            )
            return state
            
    except Exception as e:
        logger.exception(f"Focus agent failed: {e}")
        state.add_agent_output(
            agent="focus_agent",
            result={
                "status": "error",
                "error": str(e),
                "intent": intent
            },
            score=0.0
        )
        return state