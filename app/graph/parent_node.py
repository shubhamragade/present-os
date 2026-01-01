"""
Parent Agent - REAL Decision Maker (PDF-COMPLIANT)

PDF REQUIREMENTS MET:
- Makes decisions that ACTUALLY change behavior
- Coordinates multiple agents as ONE action
- Applies PAEI to modify outputs
- Links to RPM goals
- Provides unified responses
- Respects energy levels
"""

from __future__ import annotations
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, date

from app.graph.state import PresentOSState
from app.services.paei_engine import get_paei_decision  # Decision engine
from app.services.rpm_engine import compute_rpm_from_context
from app.services.energy_engine import compute_energy_from_state
from app.services.time_parser import parse_time
from app.integrations.notion_client import NotionClient
        
# Get Notion client for auto-detection

logger = logging.getLogger("presentos.parent_agent")


# COMPLETE Agent Registry (PDF Pages 6-7)
# In your ParentNode, update CATEGORY_AGENT_MAP:

CATEGORY_AGENT_MAP = {
    # Core agents
    "task": "task_agent",
    "calendar": "calendar_agent",
    "email": "email_agent",  # Full email, not just sender
    
    # Focus & Productivity
    "focus": "focus_agent",
    
    # RPM Framework
    "quest": "quest_agent",
    "map": "map_agent",
    
    # Communication & People
    "contact": "contact_agent",
    
    # Meetings (PDF: Fireflies is MANDATORY)
    "meeting": "fireflies_agent",      # For meeting scheduling/summaries
    "fireflies": "fireflies_agent",    # For transcription processing
    
    # Gamification (PDF requirement)
    "xp": "xp_agent",
    
    # Environmental (PDF Page 14-15)
    "weather": "weather_agent",  # Proactive decisions
    
    # Financial (PDF Page 20-21)
    "finance": "finance_agent",

}

READ_DOMAIN_AGENT_MAP = {
    # Information requests
    "plan_report": "plan_report_agent",
    "weather": "weather_agent",      # Different from proactive
    "research": "browser_agent",
    "report": "report_agent",
    
    # Status checks
    "xp_status": "xp_agent",           # XP agent handles status requests
    "finance_status": "finance_agent",
    "quest_status": "quest_agent",
    "meeting_summary": "fireflies_agent",
}


class ParentNode:
    """
    REAL Decision Maker that changes behavior.
    
    From PDF Page 3:
    "ONE chat interface... AI understands Calendar + Email + Reminder task...
     All happens in backend... User just sees: 'Done. Meeting scheduled... +5 Integrator XP.'"
    """
    def __init__(self):
        self.notion = NotionClient.from_env()
    
    def __call__(self, state: PresentOSState) -> PresentOSState:
        logger.info("ParentNode making REAL decisions")
        intents = state.intent.intents if state.intent else []
        read_domains = state.intent.read_domains if state.intent else []
        raw_text = state.input_text or ""
        text = raw_text.lower()
        
        # -------------------------------------------------
        # 0. DAILY MORNING CHECK (BEFORE ANYTHING ELSE)
        # -------------------------------------------------
        force_morning_check = self._check_daily_weather(state)
        
        # -------------------------------------------------
        # 1. READ-ONLY Requests (WITH FIXED XP PAYLOAD)
        # -------------------------------------------------
        if not intents:
            return self._handle_read_only(read_domains, state, raw_text)
        
        # -------------------------------------------------
        # 2. EXTRACT Decision Signals
        # -------------------------------------------------
        intent_signals = self._extract_paei_signals(intents, text)
        context = self._build_decision_context(state)
        
        
        # -------------------------------------------------
        # 3. MAKE PAEI DECISION (Changes behavior)
        # -------------------------------------------------
        paei_decision = get_paei_decision(intent_signals, context)
        logger.info(f"PAEI Decision: {paei_decision.role.value} - {paei_decision.reasoning}")
        
        # -------------------------------------------------
        # 4. AUTO-LINK RPM (PDF REQUIREMENT)
        # -------------------------------------------------
        # Get active quest and map from Notion
        try:
            active_quest_dict = self.notion.get_active_quest()
            active_map_dict = self.notion.get_active_map()
        except Exception as e:
            logger.warning(f"Failed to fetch RPM from Notion: {e}")
            active_quest_dict = None
            active_map_dict = None
        
        # AUTO-DETECT ACTIVE QUEST FROM NOTION
        if active_quest_dict and active_quest_dict.get("status") == "In Progress":
            from app.graph.state import QuestContext
            quest_id = active_quest_dict.get("id", "unknown")
            if quest_id not in state.quests:
                state.quests[quest_id] = QuestContext(
                    id=quest_id,
                    name=active_quest_dict.get("name", "Active Quest"),
                    purpose=active_quest_dict.get("purpose", ""),
                    result=active_quest_dict.get("result", ""),
                    status="active"
                )
                logger.info(f"Auto-linked to Quest: {active_quest_dict.get('name')}")
        
        # AUTO-DETECT ACTIVE MAP FROM NOTION
        if active_map_dict and active_map_dict.get("status") == "In Progress":
            from app.graph.state import MapContext
            map_id = active_map_dict.get("id", "unknown")
            if map_id not in state.maps:
                state.maps[map_id] = MapContext(
                    id=map_id,
                    name=active_map_dict.get("name", "Active MAP"),
                    quest_id=active_map_dict.get("quest_id"),
                    status="active"
                )
                logger.info(f"Auto-linked to MAP: {active_map_dict.get('name')}")

        # -------------------------------------------------
        # 5. GET RPM Context (AFTER AUTO-LINKING) - PASS RAW DICTS
        # -------------------------------------------------
        rpm_result = compute_rpm_from_context({
            "quest": active_quest_dict,  # Raw Notion dict
            "map": active_map_dict,      # Raw Notion dict
        })
        logger.info(f"RPM Result: {rpm_result.alignment_score} - {rpm_result.recommendation}")

        # -------------------------------------------------
        # 5.5 RESPECT RPM DECISION (PDF REQUIREMENT - NEW)
        # -------------------------------------------------
        if rpm_result.recommendation == "block" and not rpm_result.aligned:
            # RPM says BLOCK this action - don't proceed
            logger.warning(f"🚫 RPM blocked action: {rpm_result.reason}")
            
            # Create blocked response
            unified_response = f"❌ Action blocked: {rpm_result.reason}"
            
            state.parent_decision = {
                "instructions": [],
                "unified_response": unified_response,
                "paei_decision": {
                    "role": paei_decision.role.value,
                    "xp_amount": 0,  # No XP for blocked actions
                    "email_style": paei_decision.email_style,
                    "task_approach": paei_decision.task_approach,
                    "reasoning": f"Blocked by RPM: {rpm_result.reason}"
                },
                "is_coordinated_action": False,
                "energy_context": {},
                "rpm_context": rpm_result.__dict__,
                "was_blocked_by_rpm": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            return state  # Exit early - don't create instructions
        
        # -------------------------------------------------
        # 6. GET Energy Context
        # -------------------------------------------------
        energy_result = compute_energy_from_state(state=state, urgency=intent_signals.get("urgency", False))

        # -------------------------------------------------
        # 7. BUILD Instructions with PAEI Applied
        # -------------------------------------------------
        instructions = []
        activated_agents = set()

        for intent in intents:
            agent = CATEGORY_AGENT_MAP.get(intent.category)
            if not agent:
                continue
                
            payload = self._build_agent_payload(
                agent=agent,
                intent=intent,
                raw_text=raw_text,
                paei_decision=paei_decision,
                rpm_result=rpm_result,
                energy_result=energy_result,
                state=state
            )
            
            instructions.append({
                "agent": agent,
                "intent": intent.intent,
                "payload": payload,
                "paei_context": {
                    "role": paei_decision.role.value,
                    "email_style": paei_decision.email_style,
                    "task_approach": paei_decision.task_approach,
                    "execution_notes": paei_decision.execution_notes
                }
            })
            activated_agents.add(agent)

        instructions = self._apply_weather_decisions(instructions, state)
        
        # -------------------------------------------------
        # 7.5 ADD DAILY MORNING CHECK IF NEEDED (FIXED!)
        # -------------------------------------------------
        if force_morning_check:
            instructions.insert(0, {
                "agent": "weather_agent",
                "intent": "morning_daily_check",
                "payload": {
                    "check_surf_conditions": True,
                    "time_of_day": "morning",
                    "priority": "high"
                }
            })
        
        # -------------------------------------------------
        # 8. ADD Proactive Agents if needed
        # -------------------------------------------------
        self._add_proactive_agents(instructions, paei_decision, context, state)
        
        # -------------------------------------------------
        # 9. ADD XP Agent (ALWAYS add for action completion)
        # -------------------------------------------------
        self._add_xp_agent_if_needed(instructions, paei_decision, activated_agents)
        
        # -------------------------------------------------
        # 10. BUILD Unified Response
        # -------------------------------------------------
        unified_response = self._build_unified_response(instructions, paei_decision)
        
        # -------------------------------------------------
        # 11. RETURN Complete Decision
        # -------------------------------------------------
        state.activated_agents = list(activated_agents)
        state.parent_decision = {
            "instructions": instructions,
            "unified_response": unified_response,
            "paei_decision": {
                "role": paei_decision.role.value,
                "xp_amount": paei_decision.xp_amount,
                "email_style": paei_decision.email_style,
                "task_approach": paei_decision.task_approach,
                "reasoning": paei_decision.reasoning
            },
            "is_coordinated_action": len([i for i in instructions if i["agent"] not in ["xp_agent", "weather_agent"]]) > 1,
            "energy_context": energy_result.__dict__,
            "rpm_context": rpm_result.__dict__ if hasattr(rpm_result, "__dict__") else {},
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return state
    
    def _handle_read_only(
        self,
        read_domains: List[str],
        state: PresentOSState,
        raw_text: str
    ) -> PresentOSState:
        """Handle read-only requests WITH PROPER XP PAYLOAD"""
        
        instructions = []
        for domain in read_domains:
            agent = READ_DOMAIN_AGENT_MAP.get(domain)
            if agent:
                # ✅ Build proper payload for EACH agent type
                payload = {}
                
                if agent == "browser_agent":
                    payload = {
                        "query": raw_text,  # ✅ Pass the full research query!
                        "research_type": self._determine_research_type(raw_text),
                        "detailed": True  # ✅ Get full answer
                    }
                elif agent == "xp_agent":
                    payload = {
                        "action_type": "report_viewed",
                        "report_type": "weekly_xp_report",
                        "difficulty": "easy",
                        "duration_minutes": 5,
                        "priority": "low"
                    }
                elif agent == "weather_agent":
                    payload = {
                        "query": raw_text,
                        "detailed": False
                    }
                # Add more as needed
                
                instructions.append({
                    "agent": agent,
                    "intent": f"read_{domain}",
                    "payload": payload  # ✅ Now browser_agent gets the query!
                })
        
        state.activated_agents = [i["agent"] for i in instructions]
        state.parent_decision = {
            "instructions": instructions,
            "is_coordinated_action": False,
            
        }
        
        return state
    def _determine_research_type(self, text: str) -> str:
        """Determine research type based on query content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ["competitor", "competitive", "vs ", "compare", "alternative"]):
            return "competitive_analysis"
        elif any(word in text_lower for word in ["article", "blog", "news", "recent", "trend"]):
            return "content_curation"
        elif any(word in text_lower for word in ["price", "cost", "$", "deal", "sale", "discount"]):
            return "price_monitoring"
        elif any(word in text_lower for word in ["reddit", "twitter", "forum", "people saying", "sentiment"]):
            return "market_research"
        else:
            return "general_research"
            
            state.activated_agents = [i["agent"] for i in instructions]
            state.parent_decision = {
                "instructions": instructions,
                "is_coordinated_action": False,
                "unified_response": "Here's your requested information."
            }
            
        return state
    
    def _add_xp_agent_if_needed(
        self,
        instructions: List[Dict],
        paei_decision: Any,
        activated_agents: set
    ):
        """Add XP agent for action completion if not already present"""
        
        # Only add if we have action agents and XP agent isn't already there
        action_agents = [a for a in activated_agents if a not in ["xp_agent", "weather_agent"]]
        
        if action_agents and "xp_agent" not in activated_agents:
            # Determine XP action type based on activated agents
            action_type = "task_complete"  # Default
            
            if "calendar_agent" in activated_agents:
                action_type = "meeting_complete"
            elif "focus_agent" in activated_agents:
                action_type = "deep_work_block"
            elif "email_agent" in activated_agents:
                action_type = "task_complete"  # Email counts as task completion
            elif "quest_agent" in activated_agents:
                action_type = "task_complete"  # Quest creation counts
            
            instructions.append({
                "agent": "xp_agent",
                "intent": "award_xp",
                "payload": {
                    "action_type": action_type,  # ✅ This matches XP Engine
                    "paei": paei_decision.role.value,
                    "difficulty": "medium",
                    "duration_minutes": 60,
                    "priority": "medium",
                    "xp_amount": paei_decision.xp_amount
                }
            })
            activated_agents.add("xp_agent")
    
    def _apply_weather_decisions(self, instructions: List[Dict], state: PresentOSState) -> List[Dict]:
        """Apply weather-based proactive decisions to instructions."""
        
        if not hasattr(state, 'weather_snapshot') or not state.weather_snapshot:
            return instructions
        
        weather = state.weather_snapshot
        
        # Check for perfect surf/kite conditions
        surf_analysis = weather.get("surf_analysis", {})
        condition_type = surf_analysis.get("condition_type", "")
        
        # Pass weather context to ALL calendar instructions
        for instruction in instructions:
            if instruction["agent"] == "calendar_agent":
                # Add comprehensive weather context
                instruction["payload"]["weather_context"] = {
                    "condition_type": condition_type,
                    "rain_risk": weather.get("current", {}).get("rain_risk", "unknown"),
                    "surf_score": surf_analysis.get("score", 0),
                    "wind_knots": weather.get("current", {}).get("wind_speed_knots"),
                    "temperature_c": weather.get("current", {}).get("temperature_c"),
                    "source": "weather_agent_decision"
                }
        
        # Perfect kite conditions → block time
        if condition_type == "perfect_kite":
            instructions.append({
                "agent": "calendar_agent",
                "intent": "block_time_for_activity",
                "payload": {
                    "title": "Kitesurf Session (Perfect Conditions)",
                    "duration_minutes": 180,
                    "priority": "high",
                    "reason": "perfect_kite_conditions",
                    "weather_context": {
                        "condition_type": condition_type,
                        "surf_score": surf_analysis.get("score", 0),
                        "wind_knots": weather.get("current", {}).get("wind_speed_knots"),
                        "action": "block_time_due_to_perfect_conditions"
                    },
                    "auto_reschedule_conflicts": True,
                    "notify_user": True
                }
            })
        
        # High rain risk → suggest virtual meetings
        elif weather.get("current", {}).get("rain_risk") in ["high", "very_high"]:
            for instruction in instructions:
                if instruction["agent"] == "calendar_agent":
                    instruction["payload"]["weather_advisory"] = {
                        "suggestion": "consider_virtual_meeting",
                        "reason": "high_rain_risk",
                        "condition_type": condition_type,
                        "rain_risk": weather.get("current", {}).get("rain_risk")
                    }
        
        return instructions
    
    def _build_agent_payload(
        self,
        agent: str,
        intent: Any,
        raw_text: str,
        paei_decision: Any,
        rpm_result: Any,
        energy_result: Any,
        state: PresentOSState
    ) -> Dict[str, Any]:
        """Build payload with ACTUAL PAEI influence"""
        
        payload = dict(intent.payload or {})
        
        # ✅ XP AGENT: Use YOUR XP Engine's action types
        if agent == "xp_agent":
            # Map intent directly to XP Engine's BASE_XP_BY_ACTION keys
            intent_to_xp_action = {
                "create_task": "task_complete",
                "schedule_meeting": "meeting_complete", 
                "draft_email": "task_complete",
                "set_focus": "deep_work_block",
                "create_quest": "task_complete",
                "create_map": "task_complete",
                "create_contact": "task_complete",
                "check_weather": "task_complete",
                "process_finance": "task_complete",
                "report_viewed": "reflection",  # ✅ NEW: For read-only reports
                "award_xp": "task_complete",    # ✅ NEW: Default for XP awards
            }
            
            # Get the intent from the instruction
            intent_name = intent.intent if hasattr(intent, 'intent') else "task_complete"
            
            # Map to YOUR XP Engine's action types
            action_type = intent_to_xp_action.get(intent_name, "task_complete")
            
            # Verify it exists in BASE_XP_BY_ACTION
            valid_actions = ["task_complete", "meeting_complete", "deep_work_block", "habit_streak", "reflection"]
            if action_type not in valid_actions:
                action_type = "task_complete"  # Fallback
            
            payload.update({
                "action_type": action_type,  # ✅ This MUST match your XP Engine
                "paei": paei_decision.role.value,
                "difficulty": payload.get("difficulty", "medium"),
                "duration_minutes": payload.get("duration_minutes", 60),
                "priority": payload.get("priority", "medium"),
                "task_id": payload.get("task_id")
            })
            return payload  # Return early for XP agent
        
        # Time parsing for time-sensitive agents
        if agent in ["task_agent", "calendar_agent"]:
            time_data = parse_time(raw_text, state.timezone)
            if time_data:
                payload.update({
                    "title": time_data.get("cleaned_text", raw_text),
                    "deadline": time_data.get("deadline"),
                    "duration": time_data.get("duration", "30min")
                })
        
        # APPLY PAEI DECISION (Changes behavior)
        if agent == "email_agent":
            payload.update({
                "tone": paei_decision.email_style,
                "include_acknowledgement": paei_decision.role.value == "I",
                "use_bullet_points": paei_decision.role.value == "P",
                "vision_context": paei_decision.role.value == "E",
                "structured_format": paei_decision.role.value == "A"
            })
            
        elif agent == "task_agent":
            payload.update({
                "approach": paei_decision.task_approach,
                "time_allocation": paei_decision.calendar_buffer,
                "priority": paei_decision.priority_level,
                "include_team_context": paei_decision.role.value == "I",
                "timebox_minutes": 15 if paei_decision.role.value == "P" else 30
            })
            
        elif agent == "calendar_agent":
            payload.update({
                "buffer_minutes": 15 if paei_decision.role.value == "I" else 5,
                "allow_back_to_back": paei_decision.role.value != "I",
                "include_focus_blocks": paei_decision.role.value in ["P", "E"]
            })
        
        # Apply energy context
        if energy_result.capacity == "low":
            payload["estimated_duration_multiplier"] = 1.5
            payload["allow_extra_breaks"] = True
        
        # RPM linking
        if hasattr(rpm_result, "quest_id") and rpm_result.quest_id:
            payload["quest_id"] = rpm_result.quest_id
            payload["quest_context"] = getattr(rpm_result, "quest_context", "")
            
        if hasattr(rpm_result, "map_id") and rpm_result.map_id:
            payload["map_id"] = rpm_result.map_id
        
        return payload
    
    def _extract_paei_signals(self, intents: List[Any], text: str) -> Dict[str, bool]:
        """Extract signals for PAEI decision"""
        
        signals = {
            "urgency": any(word in text for word in ["urgent", "asap", "immediately", "now"]),
            "deadline": any(word in text for word in ["by", "due", "deadline", "tomorrow"]),
            "administrative": any(i.category in ["task", "map", "finance"] for i in intents),
            "structured": "block" in text or "schedule" in text,
            "exploratory": any(word in text for word in ["research", "explore", "learn", "discover", "brainstorm"]),
            "strategic": any(word in text for word in ["strategy", "plan", "vision", "goal", "quest"]),
            "involves_people": any(i.category in ["email", "calendar", "meeting", "contact", "fireflies"] for i in intents),
            "emotional_tone": any(word in text for word in ["sorry", "apologize", "thank", "appreciate", "frustrated", "stress", "overwhelmed"]),
            "relationship_focus": any(word in text for word in ["team", "everyone", "together", "collaborate", "partner"]),
            "execution_focus": "do" in text or "complete" in text or "finish" in text or "execute" in text,
            "documentation": "document" in text or "note" in text or "record" in text or "track" in text,
            "creative": "creative" in text or "brainstorm" in text or "idea" in text or "innovate" in text,
            "gamification": "xp" in text or "points" in text or "level" in text or "gam" in text,
            "financial": "bill" in text or "pay" in text or "money" in text or "budget" in text,
        }
        
        return signals
    
    def _build_decision_context(self, state: PresentOSState) -> Dict[str, Any]:
        """Build context for PAEI decision"""
        
        return {
            "whoop_recovery": state.whoop_recovery_score or 70,
            "team_morale": state.meta.get("team_morale", "stable"),
            "deadline_pressure": self._assess_deadline_pressure(state),
            "user_energy": state.energy_level,
            "time_of_day": self._get_time_of_day(state.timezone),
            "recent_paei_balance": state.meta.get("recent_paei_balance", {}),
            "weather_conditions": state.weather_snapshot
        }
    
    def _add_proactive_agents(
        self,
        instructions: List[Dict],
        paei_decision: Any,
        context: Dict[str, Any],
        state: PresentOSState
    ):
        """Add proactive agents based on context"""
        
        # Weather check for outdoor activities
        if (paei_decision.role.value in ["P", "E"] and 
            context.get("whoop_recovery", 70) > 60):
            
            instructions.append({
                "agent": "weather_agent",
                "intent": "proactive_schedule_check",
                "payload": {
                    "current_schedule": state.calendar.today_events,
                    "user_preferences": state.meta.get("outdoor_activities", []),
                    "paei_context": paei_decision.role.value
                }
            })
        
        # Fireflies for meetings
        if any(i["agent"] == "calendar_agent" for i in instructions):
            instructions.append({
                "agent": "fireflies_agent",
                "intent": "auto_join_meeting",
                "payload": {
                    "calendar_event": next(
                        (i["payload"] for i in instructions if i["agent"] == "calendar_agent"),
                        {}
                    )
                }
            })
    
    def _check_daily_weather(self, state: PresentOSState) -> bool:
        """
        PDF Page 14-15: Daily morning check for perfect conditions
        Returns True if weather check was added
        """
        
        # Check if it's morning (6-8am)
        hour = datetime.now().hour
        
        if 6 <= hour <= 8:  # Morning window
            # Check if we already checked today
            last_check = state.meta.get("last_weather_check_date")
            today = date.today().isoformat()
            
            if last_check != today:
                # Update last check date
                if not state.meta:
                    state.meta = {}
                state.meta["last_weather_check_date"] = today
                return True
        
        return False
    
    def _build_unified_response(
        self,
        instructions: List[Dict],
        paei_decision: Any
    ) -> str:
        """Build ONE response for coordinated actions"""
        
        action_agents = [i["agent"] for i in instructions 
                if i["agent"] not in ["xp_agent", "weather_agent", "fireflies_agent"]]

        if len(action_agents) == 1:
            agent_map = {
                "task_agent": "Task",
                "calendar_agent": "Meeting",
                "email_agent": "Email",
                "focus_agent": "Focus session",
                "finance_agent": "Financial task",
                "quest_agent": "Quest",
                "weather_agent": "Weather check"
            }
            action = agent_map.get(action_agents[0], "Action")
            
            xp_msg = f"+{paei_decision.xp_amount} {paei_decision.role.value} XP" if paei_decision.xp_amount > 0 else ""
            return f"✅ {action} scheduled. {xp_msg}".strip()
        
        else:
            actions = len(set(action_agents))
            xp_msg = f"+{paei_decision.xp_amount} {paei_decision.role.value} XP" if paei_decision.xp_amount > 0 else ""
            return f"✅ {actions} actions coordinated. {xp_msg}".strip()
    
    def _assess_deadline_pressure(self, state: PresentOSState) -> str:
        """Assess deadline pressure from tasks"""
        urgent_tasks = sum(1 for t in state.tasks.values() 
                          if t.priority == "High" and t.status != "completed")
        
        if urgent_tasks >= 3:
            return "critical"
        elif urgent_tasks >= 1:
            return "high"
        return "low"
    
    def _get_time_of_day(self, timezone: str) -> str:
        """Get time of day for context"""
        hour = datetime.now().hour
        
        if hour < 12:
            return "morning"
        elif hour < 17:
            return "afternoon"
        else:
            return "evening"


# Global instance
_parent_node = ParentNode()


def run_parent_node(state: PresentOSState) -> PresentOSState:
    """Entry point for execution graph"""
    return _parent_node(state)