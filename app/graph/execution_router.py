from __future__ import annotations
import logging
from typing import Dict, Any, List

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient

logger = logging.getLogger("presentos.execution_router")


class ExecutionRouter:
    """
    Executes PAEI-driven instructions.
    """
    
    def __init__(self, notion: NotionClient):
        self.notion = notion
        self.agent_runners = self._initialize_runners()
        
    def _initialize_runners(self) -> Dict[str, Any]:
        """Initialize all agent runners - ADD browser_agent"""
        # Import here to avoid circular imports
        from app.graph.nodes.calendar_agent import run_calendar_node
        from app.graph.nodes.task_agent import run_task_node
        from app.graph.nodes.email_agent import run_email_node
        from app.graph.nodes.email_sender_agent import run_email_sender_node
        from app.graph.nodes.contact_agent import run_contact_node
        from app.graph.nodes.quest_agent import run_quest_node
        from app.graph.nodes.map_agent import run_map_node
        from app.graph.nodes.plan_report_agent import run_plan_report_node
        from app.graph.nodes.research_agent import run_research_node
        from app.graph.nodes.browser_agent import run_browser_node  # ✅ ADD THIS
        from app.graph.nodes.focus_agent import run_focus_node
        from app.graph.nodes.weather_agent import run_weather_node
        from app.graph.nodes.meeting_agent import run_meeting_node
        from app.graph.nodes.report_agent import run_report_node
        from app.graph.nodes.xp_agent import run_xp_node
        from app.graph.nodes.fireflies_agent import run_fireflies_node
        from app.graph.nodes.finance_agent import run_finance_node
        
        return {
            "calendar_agent": lambda s: run_calendar_node(s, self.notion),
            "task_agent": lambda s: run_task_node(s, self.notion),
            "email_agent": run_email_node,
            "email_sender_agent": run_email_sender_node,
            "contact_agent": run_contact_node,
            "quest_agent": lambda s: run_quest_node(s, self.notion),
            "map_agent": lambda s: run_map_node(s, self.notion),
            "plan_report_agent": lambda s: run_plan_report_node(s, self.notion),
            "research_agent": run_research_node,  # For synthesis
            "browser_agent": run_browser_node,    # ✅ ADD THIS - for searching
            "focus_agent": run_focus_node,
            "weather_agent": run_weather_node,
            "meeting_agent": run_meeting_node,
            "fireflies_agent": run_fireflies_node,
            "report_agent": lambda s: run_report_node(s, self.notion),
            "xp_agent": lambda s: run_xp_node(s, self.notion),
        }
    
    def __call__(self, state: PresentOSState) -> PresentOSState:
        """Execute instructions with PAEI awareness"""
        
        decision = state.parent_decision or {}
        instructions = decision.get("instructions", [])
        
        if not instructions:
            return state
        
        # Track execution results
        execution_results = []
        
        # Execute primary agents (not XP/Weather/Fireflies first)
        primary_agents = [i for i in instructions 
                         if i["agent"] not in ["xp_agent", "weather_agent", "fireflies_agent"]]
        
        for instruction in primary_agents:
            agent = instruction["agent"]
            runner = self.agent_runners.get(agent)
            
            if not runner:
                logger.warning(f"No runner for agent: {agent}")
                continue
            
            # Pass PAEI context to agent
            state = self._inject_paei_context(state, instruction)
            
            logger.info(f"Executing {agent} with PAEI: {instruction.get('paei_context', {}).get('role', 'P')}")
            
            try:
                result = runner(state)
                if result is not None:
                    state = result
                    execution_results.append({
                        "agent": agent,
                        "success": True,
                        "paei_role": instruction.get("paei_context", {}).get("role", "P")
                    })
            except Exception as e:
                logger.error(f"Agent {agent} failed: {e}")
                execution_results.append({
                    "agent": agent,
                    "success": False,
                    "error": str(e)
                })
        
        # Execute proactive agents (weather, fireflies)
        proactive_agents = [i for i in instructions 
                          if i["agent"] in ["weather_agent", "fireflies_agent"]]
        
        for instruction in proactive_agents:
            agent = instruction["agent"]
            runner = self.agent_runners.get(agent)
            
            if runner:
                try:
                    result = runner(state)
                    if result is not None:
                        state = result
                except Exception as e:
                    logger.error(f"Proactive agent {agent} failed: {e}")
        
        # Always execute XP agent last
        xp_instruction = next((i for i in instructions if i["agent"] == "xp_agent"), None)
        if xp_instruction:
            runner = self.agent_runners.get("xp_agent")
            if runner:
                try:
                    result = runner(state)
                    if result is not None:
                        state = result
                except Exception as e:
                    logger.error(f"XP agent failed: {e}")
        
        # Store execution summary
        state.meta["execution_summary"] = {
            "total_agents": len(execution_results),
            "successful": sum(1 for r in execution_results if r["success"]),
            "paei_distribution": self._calculate_paei_distribution(execution_results),
            "is_coordinated": decision.get("is_coordinated_action", False)
        }
        
        return state
    
    def _inject_paei_context(self, state: PresentOSState, instruction: Dict) -> PresentOSState:
        """Inject PAEI context into state for agent use"""
        
        paei_context = instruction.get("paei_context", {})
        if paei_context and not state.meta.get("current_paei_context"):
            state.meta["current_paei_context"] = paei_context
        
        return state
    
    def _calculate_paei_distribution(self, results: List[Dict]) -> Dict[str, float]:
        """Calculate PAEI distribution from execution"""
        
        if not results:
            return {"P": 0.25, "A": 0.25, "E": 0.25, "I": 0.25}
        
        role_counts = {"P": 0, "A": 0, "E": 0, "I": 0}
        total = len(results)
        
        for result in results:
            role = result.get("paei_role", "P")
            if role in role_counts:
                role_counts[role] += 1
        
        return {
            role: count / total
            for role, count in role_counts.items()
        }