# app/graph/parent_response_node.py
from __future__ import annotations
import logging
import os
from typing import List, Dict, Any

from openai import OpenAI
from app.graph.state import PresentOSState, PAEIRole

logger = logging.getLogger("presentos.parent_response")

_client: OpenAI | None = None

def _get_llm() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client

def _llm_complete(prompt: str) -> str:
    client = _get_llm()
    resp = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        messages=[
            {
                "role": "system",
                "content": (
                    "You are Martin (PresentOS), a calm, empathetic, and professional "
                    "personal assistant (co-pilot). Your goal is to speak naturally "
                    "and warmly. Acknowledge successful actions with a brief natural sentence, "
                    "then use bullet points for specific details if multiple things were done. "
                    "Always mention XP awards naturally or at the end. "
                    "Tone: Professional, efficient, slightly warm co-pilot."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=350,
    )
    return resp.choices[0].message.content

def run_parent_response_node(state: PresentOSState) -> PresentOSState:
    """
    Parent Response Node - Martin Persona Implementation
    """
    
    outputs = state.agent_outputs or []
    
    if not outputs:
        decision = state.parent_decision or {}
        instructions = decision.get("instructions", [])
        
        if instructions:
            state.final_response = _generate_response_from_instructions(instructions, decision)
            return state
        
        # Default greeting if no actions taken
        state.final_response = "All set, sir! Let me know if you'd like to do anything else."
        state.response_payload = {"status": "no_action"}
        return state
    
    # 1. Gather results into categories
    summary_data = []
    xp_awards = []
    
    for out in outputs:
        agent = out.agent_name
        res = out.result or {}
        
        if agent == "xp_agent":
            # 1. Handle Full XP Summary (if available)
            if "summary" in res:
                s = res["summary"]
                summary_data.append(f"XP STATUS REPORT:")
                summary_data.append(f"• Today's XP: {s.get('today', 0)}")
                summary_data.append(f"• This Week: {s.get('week', 0)}")
                summary_data.append(f"• This Month: {s.get('month', 0)}")
                summary_data.append(f"• Total XP: {s.get('total', 0)}")
                if s.get("focus_recommendation"):
                    summary_data.append(f"• Focus: {s.get('focus_recommendation')} is your lowest area.")
                    summary_data.append(f"• Suggestion: {s.get('focus_message', 'Keep pushing!')}")
            
            # 2. Handle Immediate XP Award
            paei = res.get('paei')
            if not paei or paei == "None":
                paei = "Active" # Default if missing
            xp_awards.append(f"+{res.get('xp', 0)} {paei} XP ({res.get('reason', 'successful task completion')})")
            continue
            
        # Agent-specific natural language mapping
        if agent == "task_agent" and res.get("action") == "task_created":
            title = res.get("title") or "Task"
            summary = f"Task added: '{title}'"
            if res.get("quest_name"):
                summary += f" (Linked to Quest: '{res.get('quest_name')}')"
            summary_data.append(summary)
            
        elif agent == "calendar_agent":
            action = res.get("action")
            if action == "created_event" or action == "scheduled_meeting":
                summary_data.append(f"Meeting scheduled: {res.get('event', {}).get('summary', 'New event')}")
            elif action == "blocked_time":
                summary_data.append(f"Time blocked for focus ({res.get('slot_score', 0.0):.0%} energy match)")
            elif action == "rescheduled_event":
                summary_data.append("Meeting rescheduled to a better slot to resolve conflicts")
                
        elif agent in ["email_agent", "email_sender_agent"]:
            action = res.get("action") or res.get("status")
            if action == "email_sent":
                recipient = res.get("recipient", "recipient")
                subject = res.get("subject", "Message")
                preview = res.get("body_preview", "")
                summary_data.append(f"✉️ Email sent to {recipient}: '{subject}'")
                if preview:
                    summary_data.append(f"Preview: {preview[:80]}...")
            elif action == "emails_checked" or action == "inbox_scanned":
                count = res.get("count") or res.get("emails_found") or 0
                scanned_items = res.get("scanned_items", [])
                
                if count > 0:
                    summary_data.append(f"📬 Checked inbox: {count} unread emails")
                    # Show first 3 emails
                    for i, email in enumerate(scanned_items[:3], 1):
                        subject = email.get("subject", "No subject")
                        sender = email.get("from", "Unknown")
                        # Clean sender (extract name or email)
                        if "<" in sender:
                            sender = sender.split("<")[0].strip()
                        summary_data.append(f"  {i}. {subject[:50]}{'...' if len(subject) > 50 else ''}")
                        summary_data.append(f"     From: {sender[:40]}")
                    
                    if count > 3:
                        summary_data.append(f"  ... and {count - 3} more")
                else:
                    summary_data.append(f"📭 Inbox checked: No unread emails")
                    
            elif action == "draft_created":
                 summary_data.append(f"Draft created for {res.get('to', 'recipient')}: '{res.get('email_preview', 'Reply')[:60]}...'")
            elif action == "email_send_failed":
                summary_data.append(f"⚠️ Email send failed: {res.get('error', 'Unknown error')}")



        elif agent in ["browser_agent", "research_agent"]:
            action = res.get("action")
            if action == "search_completed" or action == "research_synthesized":
                query = res.get("query") or "your research"
                answer = res.get("result", {}).get("answer") or res.get("summary") or "Research complete"
                summary_data.append(f"Research summary for '{query}': {answer[:200]}...")

        elif agent == "weather_agent":
            action = res.get("action") or res.get("status")
            if action == "weather_intelligence_report":
                advisory = res.get("advisory", {})
                curr = advisory.get("current", {})
                cond = curr.get("condition", "clear")
                summary_data.append(f"Weather conditions: {cond} ({curr.get('temperature_c', '??')}°C)")
                if advisory.get("surf_analysis", {}).get("condition_type") in ["perfect_kite", "good_surf"]:
                    summary_data.append(f"Proactive: Conditions are {advisory['surf_analysis']['condition_type']}!")
            elif action == "read_only_forecast":
                fc = res.get("forecast", {})
                summary_data.append(f"🌤️ Weather: {fc.get('condition', 'Conditions looking good')}")

        elif agent == "focus_agent":
            action = res.get("action")
            if action == "focus_enabled":
                # Extract detailed timing and context
                duration = res.get("duration_minutes", 60)
                start_time = res.get("start_time", "now")
                end_time = res.get("end_time", "")
                whoop_recovery = res.get("whoop_recovery", 70)
                energy_level = res.get("energy_level", "medium")
                protections = res.get("protections", {})
                deep_work = res.get("deep_work", False)
                
                # Build detailed focus summary
                session_type = "Deep work" if deep_work else "Focus"
                time_block = f"{start_time} – {end_time}" if end_time else f"{duration} min"
                
                # Energy context message
                energy_msg = ""
                if whoop_recovery >= 75:
                    energy_msg = f"High energy detected ({whoop_recovery}% recovery) — perfect slot"
                elif whoop_recovery >= 60:
                    energy_msg = f"Based on {whoop_recovery}% recovery — good for deep work"
                else:
                    energy_msg = f"Low energy ({whoop_recovery}% recovery) — consider shorter session"
                
                # Protections message
                protection_items = []
                if protections.get("calendar_blocked"):
                    protection_items.append("Calendar blocked")
                if protections.get("notifications_silenced"):
                    protection_items.append("notifications silenced")
                protections_msg = ", ".join(protection_items) if protection_items else "Protections active"
                
                # Build full summary
                summary_data.append(f"{session_type} session: {time_block}")
                summary_data.append(f"{protections_msg}")
                summary_data.append(f"{energy_msg}")
            elif action == "focus_disabled":
                summary_data.append("Focus mode ended")
            else:
                summary_data.append(f"Focus mode active: Blocked {res.get('duration_minutes', 'the session')} for deep work")

            
        elif agent == "finance_agent":
            action = res.get("action")
            if action == "expense_logged":
                summary_data.append(f"Logged expense: ${res.get('amount')} at {res.get('merchant')}")
            elif action == "budget_checked":
                summary_data.append(f"Budget status: {res.get('summary', 'On track')}")
            elif action == "portfolio_checked":
                summary_data.append(f"Portfolio update: {res.get('summary')}")
            
        elif agent == "quest_agent":
            summary_data.append(f"New Quest initialized: '{res.get('quest_name', 'Goal')}'")

        elif agent == "fireflies_agent":
            summary_data.append(f"Meeting summary processed: {res.get('summary', 'Notes saved to Notion')[:100]}...")
            if res.get("tasks_extracted"):
                summary_data.append(f"Extracted {len(res['tasks_extracted'])} tasks from the meeting")

        elif agent == "contact_agent":
            status = res.get("status")
            if status == "contact_found":
                name = res.get("name")
                email = res.get("email") or "N/A"
                phone = res.get("phone") or "N/A"
                notes = res.get("notes") or "No notes on file"
                summary_data.append(f"Contact info for {name}:")
                summary_data.append(f"• Email: {email}")
                summary_data.append(f"• Phone: {phone}")
                summary_data.append(f"• Notes: {notes}")
            elif status == "contact_updated":
                name = res.get("name")
                action = res.get("action")
                note = res.get("note")
                if action == "note_saved":
                    summary_data.append(f"Note saved on {name}: '{note}'")
                else:
                    summary_data.append(f"Contact record updated for {name}")
            elif status == "contact_missing":
                summary_data.append(f"Could not find a contact record for {res.get('contact_name') or 'requested person'}")

        elif agent == "plan_report_agent":
            action = res.get("action")
            if action == "daily_plan":
                tasks = res.get("tasks", [])
                count = len(tasks)
                summary_data.append(f"📅 Daily plan loaded: {count} tasks found")
                if tasks:
                    titles = [t.get("title", "Task") for t in tasks]
                    preview = ", ".join(titles[:3])
                    if len(titles) > 3:
                        preview += "..."
                    summary_data.append(preview)
            
    # 2. Generate Prompt for Martin
    prompt = f"""
USER INPUT: {state.input_text}
ACTIONS COMPLETED:
{chr(10).join(f"- {s}" for s in summary_data)}

XP AWARDS:
{chr(10).join(xp_awards)}

INSTRUCTIONS:
Generate a response in Martin's natural persona.
- Start with a warm, natural confirmation (e.g. "Got it!", "All set, sir.", "Certainly.")
- Use bullet points if there are multiple actions.
- Include a 1-sentence clean summary for research if applicable.
- End with the XP award line exactly as formatted in the XP AWARDS section above.
- Add an optional closing question like "Anything else?" if appropriate.

EXAMPLE FORMAT:
"Got it!
• Deep work blocked 9–12 tomorrow
• 10am call moved to 2pm
+10 Producer XP (focus protection)
Anything else?"
"""

    try:
        response = _llm_complete(prompt)
        state.final_response = response.strip()
    except Exception:
        logger.exception("LLM response generation failed")
        state.final_response = "I've processed your request successfully, sir. Actions are reflecting in your dashboard."
    
    state.response_payload = {
        "status": "completed",
        "summary": summary_data,
        "xp": xp_awards
    }
    
    return state

def _generate_response_from_instructions(instructions: List[Dict], decision: Dict) -> str:
    """Fallback for when agents haven't returned yet or simple decisions"""
    return "Certainly, sir. I'm coordinating those actions for you now."