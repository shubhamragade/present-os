"""
Weather Agent for PresentOS

Responsible for:
- Fetching weather data for given location/time
- Analyzing conditions for outdoor activities
- Providing advisory signals to ParentAgent
- Never scheduling directly (advisory only)
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from app.utils.instruction_utils import get_instruction
from app.graph.state import PresentOSState
from app.integrations.weather_client import get_forecast, get_surf_forecast

logger = logging.getLogger("presentos.weather_agent")

# Activity-specific thresholds
PERFECT_KITE_WIND = (15, 25)  # knots
GOOD_SURF_WIND = (10, 30)     # knots
MIN_SWELL_FEET = 3.0          # feet
MAX_SWELL_FEET = 6.0

DEFAULT_LOCATION = {
    "city": "Pune",
    "country": "IN",
    "state": "Maharashtra"
}


def _get_surf_decision_logic(forecast: Dict, surf_data: Dict) -> Dict[str, Any]:
    """Determine surf/kite conditions based on weather data."""
    
    wind_knots = forecast.get("wind_speed_knots", 0)
    condition = forecast.get("condition", "").lower()
    swell_feet = surf_data.get("swell_feet", 0)
    tide_state = surf_data.get("tide", "unknown")
    
    decision = {
        "condition_type": "terrible",
        "priority": "low",
        "recommended_actions": [],
        "calendar_impact": "no_change",
        "duration_hours": 0,
        "confidence": 0.6
    }
    
    # Perfect kitesurf conditions (15-25 knots)
    if PERFECT_KITE_WIND[0] <= wind_knots <= PERFECT_KITE_WIND[1]:
        decision.update({
            "condition_type": "perfect_kite",
            "priority": "high",
            "recommended_actions": ["block_calendar_time"],
            "calendar_impact": "block_time",
            "duration_hours": 3.0,
            "confidence": 0.9
        })
    
    # Good surf conditions (3-6 feet swell, clean weather)
    elif (MIN_SWELL_FEET <= swell_feet <= MAX_SWELL_FEET and 
          condition in ["clear", "few clouds"]):
        decision.update({
            "condition_type": "good_surf",
            "priority": "medium",
            "recommended_actions": ["suggest_time_block"],
            "calendar_impact": "suggest_time",
            "duration_hours": 2.0,
            "confidence": 0.75
        })
    
    # Good beach weather (clear skies, light wind)
    elif condition in ["clear", "few clouds", "scattered clouds"] and wind_knots < 10:
        decision.update({
            "condition_type": "beach_day",
            "priority": "medium",
            "recommended_actions": ["suggest_outdoor_work"],
            "calendar_impact": "suggest_time",
            "duration_hours": 1.5,
            "confidence": 0.7
        })
    
    # Dangerous conditions
    elif condition in ["thunderstorm", "heavy rain", "squall", "tornado"]:
        decision.update({
            "condition_type": "terrible",
            "priority": "high",
            "recommended_actions": ["keep_indoor_schedule"],
            "calendar_impact": "no_change",
            "confidence": 0.95
        })
    
    return decision


def _get_proactive_recommendations(decision: Dict, context: Dict) -> Dict[str, Any]:
    """Generate proactive recommendations for schedule adjustments."""
    
    if decision["condition_type"] == "perfect_kite":
        return {
            "type": "calendar_adjustment",
            "action": "block_time_with_high_priority",
            "time_of_day": "morning",
            "duration_minutes": 180,
            "message": "Perfect kitesurf conditions detected. Recommend blocking morning.",
            "urgency": "high",
            "auto_reschedule": True
        }
    
    elif decision["condition_type"] == "good_surf":
        return {
            "type": "calendar_suggestion",
            "action": "suggest_flexible_block",
            "time_of_day": "afternoon",
            "duration_minutes": 120,
            "message": "Good surf conditions available. Would you like to schedule a session?",
            "urgency": "medium",
            "requires_confirmation": True
        }
    
    elif decision.get("rain_risk") in ["high", "very_high"]:
        return {
            "type": "meeting_adjustment",
            "action": "convert_to_virtual",
            "message": "High rain risk detected. Suggest converting outdoor meetings to virtual."
        }
    
    return {
        "type": "advisory_only",
        "action": "no_change_needed",
        "message": "Conditions are normal, no schedule adjustments needed."
    }


def run_weather_node(state: PresentOSState) -> PresentOSState:
    """
    Weather Agent - Provides weather intelligence for decision making.
    """
    
    # Get instruction - FIX THIS SECTION
    instruction = None
    try:
        # Try to get instruction from state
        if hasattr(state, 'parent_decision') and state.parent_decision:
            for instr in state.parent_decision.get("instructions", []):
                if instr.get("agent") == "weather_agent":
                    instruction = instr
                    break
    except:
        instruction = None
    
    # If no instruction found, check activated_agents
    if not instruction and "weather_agent" not in state.activated_agents:
        return state
    
    # Extract payload
    weather_instruction = instruction.get("payload", {}) if instruction else {}
    
    # Handle read-only weather requests (e.g., "Should I go kitesurfing?")
    intent = instruction.get("intent", "") if instruction else ""
    if intent == "read_weather" or not weather_instruction:
        # Simple read-only response
        location = weather_instruction.get("location") or DEFAULT_LOCATION
        forecast = get_forecast(location) or {}
        
        state.add_agent_output(
            agent="weather_agent",
            result={
                "status": "read_only_forecast",
                "forecast": forecast,
                "type": "weather_report",
                "metadata": {"intent": "read_only"}
            },
            score=0.9,
        )
        
        logger.info(f"WeatherAgent: Read-only forecast for {location.get('city', 'Pune')}")
        return state
    
    # Rest of your existing proactive logic continues here...
    location = weather_instruction.get("location") or DEFAULT_LOCATION
    intent_context = weather_instruction.get("intent_context", "general")
    
    decision = state.parent_decision or {}
    instructions = decision.get("instructions", [])
    
    # Find weather agent instruction
    weather_instruction = None
    for instr in instructions:
        if instr.get("agent") == "weather_agent":
            weather_instruction = instr.get("payload", {})
            break
    
    if not weather_instruction:
        # Try to get from instruction utils as fallback
        try:
            weather_instruction = get_instruction(state, "weather_agent")
        except:
            weather_instruction = {}
    
    if not weather_instruction:
        return state

    location = weather_instruction.get("location") or DEFAULT_LOCATION
    intent_context = weather_instruction.get("intent_context", "general")
    scheduled_for = weather_instruction.get("scheduled_for")
    check_surf = weather_instruction.get("check_surf_conditions", True)

    try:
        # Get basic weather data
        forecast = get_forecast(location)
        
        if not forecast:
            state.add_agent_output(
                agent="weather_agent",
                result={
                    "status": "no_data", 
                    "location": location,
                    "action": "weather_intelligence_report",
                    "advisory": {
                        "type": "weather_error",
                        "message": "No weather data available",
                        "recommendation": "Proceed with normal schedule"
                    }
                },
                score=0.0,
            )
            return state

        # Get surf-specific data if requested
        surf_data = {}
        if check_surf:
            surf_data = get_surf_forecast(location) or {}
        
        # Analyze conditions
        surf_decision = _get_surf_decision_logic(forecast, surf_data)
        proactive_rec = _get_proactive_recommendations(
            {**forecast, **surf_decision},
            {"intent_context": intent_context, "scheduled_for": scheduled_for}
        )
        
        # Build advisory output
        advisory = {
            "type": "weather_intelligence",
            
            # Location
            "location": {
                "city": location.get("city", "Pune"),
                "country": location.get("country", "IN"),
                "formatted": f"{location.get('city', 'Pune')}, {location.get('country', 'IN')}"
            },
            
            # Current Conditions
            "current": {
                "condition": forecast.get("condition"),
                "temperature_c": forecast.get("temperature_c"),
                "rain_risk": forecast.get("rain_risk"),
                "wind_speed_knots": forecast.get("wind_speed_knots"),
                "description": forecast.get("description")
            },
            
            # Surf Analysis
            "surf_analysis": {
                "condition_type": surf_decision["condition_type"],
                "wind_knots": forecast.get("wind_speed_knots"),
                "swell_feet": surf_data.get("swell_feet"),
                "tide": surf_data.get("tide"),
                "score": forecast.get("surf_score", 0),
                "decision_logic": surf_decision
            },
            
            # Proactive Intelligence
            "proactive_intelligence": proactive_rec,
            
            # Context
            "intent_context": intent_context,
            "scheduled_for": scheduled_for,
            "check_time": datetime.utcnow().isoformat()
        }
        
        # Calculate confidence
        confidence = surf_decision["confidence"]
        if surf_data.get("source") == "surfline":
            confidence = min(confidence + 0.1, 0.95)
        
        # Emit advisory - FIXED LINE 231: Remove 'metadata' parameter
        state.add_agent_output(
            agent="weather_agent",
            result={
                "action": "weather_intelligence_report",
                "advisory": advisory,
                "parent_agent_signals": {
                    "should_consider_blocking_time": surf_decision["condition_type"] in ["perfect_kite", "good_surf"],
                    "should_suggest_virtual_meetings": forecast.get("rain_risk") in ["high", "very_high"],
                    "priority": surf_decision["priority"]
                },
                # Include metadata INSIDE the result, not as separate parameter
                "metadata": {
                    "feature": "environmental_decision_making",
                    "location": location.get("city", "Pune"),
                    "confidence": confidence
                }
            },
            score=round(confidence, 3),
        )
        
        # Store in state for other agents
        state.weather_snapshot = advisory
        
        logger.info(f"WeatherAgent: {surf_decision['condition_type']} (confidence: {confidence})")
        
        return state

    except Exception as e:
        logger.exception("WeatherAgent failed")
        
        state.add_agent_output(
            agent="weather_agent",
            result={
                "status": "error_fallback",
                "error": str(e)[:200],
                "advisory": {
                    "type": "weather_error",
                    "message": "Using fallback data",
                    "recommendation": "Proceed with normal schedule"
                },
                "metadata": {
                    "error": True,
                    "error_message": str(e)[:200]
                }
            },
            score=0.3,
        )
        return state