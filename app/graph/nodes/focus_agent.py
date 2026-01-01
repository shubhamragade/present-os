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
    whoop_recovery = getattr(state, 'whoop_recovery_score', 70)
    
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


def _schedule_focus_block(state: PresentOSState, focus_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Schedule focus block via calendar agent
    Returns calendar event details
    """
    
    # Build calendar event
    event_data = {
        "title": f"🧠 Focus Time: {'Deep Work' if focus_config.get('deep_work') else 'Concentration'}",
        "description": f"Focus session scheduled by PresentOS Focus Agent\n"
                      f"Energy: {focus_config.get('energy_context', 'normal')}\n"
                      f"Policies: {focus_config.get('policies', {}).get('interruption_allowed', 'normal')}",
        "duration_minutes": focus_config.get("duration_minutes", 60),
        "focus_mode": True,
        "deep_work": focus_config.get("deep_work", False),
        "auto_decline_conflicts": focus_config.get("deep_work", False),
        "source": "focus_agent"
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
        "calendar_action_added": True
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
        if intent == "enable_focus_mode":
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
            
            # Build result
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
                "paei_context": paei_context
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