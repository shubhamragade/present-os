"""
Finance Agent - PDF COMPLIANT
Responsible for:
- Logging expenses (Notion API)
- Checking budget status (Read-only Notion)
- Awarding Admin XP (Integrator checks balance)
"""

from __future__ import annotations
import logging
from datetime import datetime
from typing import Dict, Any

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.finance_agent")

def run_finance_node(state: PresentOSState) -> PresentOSState:
    """
    Finance Agent Node
    """
    instruction = get_instruction(state, "finance_agent")
    if not instruction:
        return state

    intent = instruction.get("intent")
    payload = instruction.get("payload", {})

    logger.info(f"FinanceAgent triggered: {intent}")
    
    try:
        notion = NotionClient.from_env()
        
        # Check if expenses DB is configured
        if not notion.db_ids.get("expenses"):
            state.add_agent_output(
                agent="finance_agent",
                result={
                    "status": "error",
                    "error": "NOTION_DB_EXPENSES_ID not set in .env"
                },
                score=0.0
            )
            return state

        if intent == "log_expense":
            # Extract details
            merchant = payload.get("merchant", "Unknown Merchant")
            amount = float(payload.get("amount", 0.0))
            category = payload.get("category", "General")
            
            # Log to Notion
            res = notion.create_expense(
                merchant=merchant,
                amount=amount,
                category=category,
                status="Paid",
                date=datetime.utcnow()
            )
            
            # Award Admin XP (PDF Goal: Gamify admin tasks)
            xp_amount = 5
            state.planned_actions.append({
                "type": "xp_event",
                "paei": "A", # Admin XP
                "reason": f"Logged expense: {merchant}",
                "amount": xp_amount,
                "source": "finance_agent"
            })
            
            state.add_agent_output(
                agent="finance_agent",
                result={
                    "action": "expense_logged",
                    "merchant": merchant,
                    "amount": amount,
                    "page_id": res.get("id"),
                    "xp_awarded": xp_amount
                },
                score=1.0
            )
            
        elif intent in ["check_budget", "check_finance", "read_finance_status"]:
            from app.integrations.finance_client import FinanceClient
            fin_client = FinanceClient()
            status = fin_client.check_budget_status()
            
            # Build message based on status
            if status["status"] == "ok":
                message = f"✅ Budget on track! Spent ${status['total_spent']:,.0f} of ${status['total_limit']:,.0f} (${status['remaining']:,.0f} remaining)"
            elif status["status"] == "warning":
                overruns = [f"{o['category']} (+${o['amount']:.0f})" for o in status.get("overruns", [])]
                warnings = [f"{w['category']} ({w['percent']:.0f}%)" for w in status.get("warnings", [])]
                
                if overruns:
                    message = f"⚠️ Budget overrun: {', '.join(overruns)}. Total spent: ${status['total_spent']:,.0f}"
                    # Auto-create task for overrun
                    state.planned_actions.append({
                        "type": "create_task",
                        "title": f"Review budget overrun: {overruns[0]}",
                        "priority": "High",
                        "paei": "A"
                    })
                else:
                    message = f"⚠️ Approaching budget limit: {', '.join(warnings)}"
            elif status["status"] == "critical":
                overruns = [f"{o['category']} (+${o['amount']:.0f})" for o in status.get("overruns", [])]
                message = f"🚨 Critical: Multiple budget overruns! {', '.join(overruns)}. Spent ${status['total_spent']:,.0f} of ${status['total_limit']:,.0f}"
                # Auto-create high priority review task
                state.planned_actions.append({
                    "type": "create_task",
                    "title": "URGENT: Review budget - multiple overruns detected",
                    "priority": "High",
                    "paei": "A"
                })
            else:
                message = f"Budget status: {status['status']}"
            
            state.add_agent_output(
                agent="finance_agent",
                result={
                    "action": "budget_checked",
                    "status": status["status"],
                    "total_spent": status.get("total_spent", 0),
                    "total_limit": status.get("total_limit", 0),
                    "remaining": status.get("remaining", 0),
                    "overruns": status.get("overruns", []),
                    "by_category": status.get("by_category", {}),
                    "summary": message
                },
                score=1.0
            )

        elif intent == "check_portfolio":
            from app.integrations.finance_client import FinanceClient
            fin_client = FinanceClient()
            summary = fin_client.get_portfolio_summary()
            
            state.add_agent_output(
                agent="finance_agent",
                result={
                    "action": "portfolio_checked",
                    "total_value": summary["total_value"],
                    "day_change": summary["day_change"],
                    "summary": f"Portfolio value: ${summary['total_value']:,} ({summary['day_change']:+}%)"
                },
                score=1.0
            )
            
        else:
            state.add_agent_output(
                agent="finance_agent",
                result={"status": "ignored", "reason": "unknown_intent"},
                score=0.0
            )

    except Exception as e:
        logger.exception("FinanceAgent failed")
        state.add_agent_output(
            agent="finance_agent",
            result={"status": "error", "error": str(e)},
            score=0.0
        )
        
    return state