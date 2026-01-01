# app/graph/parent_response_node.py
from __future__ import annotations
import logging
import os
from typing import List, Dict

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
                    "You are PresentOS (Martin), a calm, empathetic, and professional "
                    "personal assistant. Speak naturally and warmly, like a trusted "
                    "co-pilot who helps the user stay aligned, balanced, and confident. "
                    "Acknowledge successful actions and mention XP awards when applicable."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.4,
        max_tokens=250,  # Increased for research responses
    )
    return resp.choices[0].message.content

def run_parent_response_node(state: PresentOSState) -> PresentOSState:
    """
    Parent Response Node (FIXED - PDF-COMPLIANT)
    
    ROLE: Convert executed agent outputs into user-facing language
    """
    
    # Check if we have agent outputs
    outputs = state.agent_outputs or []
    
    if not outputs:
        # No outputs but parent decision exists? Check instructions
        decision = state.parent_decision or {}
        instructions = decision.get("instructions", [])
        
        if instructions:
            # We have instructions but no outputs - something executed
            # Generate response based on instructions
            state.final_response = _generate_response_from_instructions(instructions, decision)
            return state
        
        state.final_response = "All set! Let me know if you'd like to do anything else."
        state.response_payload = {"status": "no_action"}
        return state
    
    # -------------------------------------------------
    # 2. STRUCTURED SUMMARY FROM AGENT OUTPUTS
    # -------------------------------------------------
    summary: List[str] = []
    has_research = False
    research_data = {}
    
    for out in outputs:
        r = out.result or {}
        agent_name = out.agent_name  # FIXED: Use agent_name not agent
        
        # BROWSER_AGENT HANDLER
        if agent_name == "browser_agent":
            has_research = True
            if r.get("action") == "search_completed":
                query = r.get("query", "your topic")
                result_data = r.get("result", {})
                success = result_data.get("success", False)
                sources_count = result_data.get("sources_count", 0)
                answer = result_data.get("answer", "")
                
                if success and answer:
                    # Store research data for rich response
                    research_data = {
                        "query": query,
                        "answer": answer,
                        "sources_count": sources_count,
                        "preview": answer[:400] + "..." if len(answer) > 400 else answer
                    }
                    
                    summary.append(f"📚 Research completed: {query}")
                    summary.append(f"Found {sources_count} credible sources")
                else:
                    summary.append("Research encountered an issue. Please try again.")
            continue
            
        # RESEARCH_AGENT HANDLER  
        elif agent_name == "research_agent":
            has_research = True
            if r.get("action") == "research_synthesized":
                insights = r.get("insights", {})
                key_points = insights.get("key_points", [])
                recommendations = insights.get("recommendations", [])
                confidence = insights.get("confidence", 0.7)
                
                summary.append(f"🧠 Research synthesized ({confidence:.0%} confidence)")
                if key_points:
                    summary.append(f"Key insights: {len(key_points)} identified")
                if recommendations:
                    summary.append(f"Actionable recommendations: {len(recommendations)}")
            continue
            
        # WEATHER_AGENT HANDLER
        elif agent_name == "weather_agent":
            condition = r.get("condition", "")
            confidence = r.get("confidence", 0.0)
            if confidence > 0.5:
                summary.append(f"🌤️ Weather: {condition}")
            else:
                summary.append("🌤️ Weather data updated")
            continue
            
        # EXISTING HANDLERS
        elif r.get("action") == "task_created":
            task_id = r.get("task_id", "")
            paei_role = out.paei_role or PAEIRole.PRODUCER
            summary.append(f"✅ Task created")
            
            # Add XP info if available
            if state.current_paei_context:
                xp_amount = state.current_paei_context.xp_amount
                if xp_amount > 0:
                    summary.append(f"+{xp_amount} {state.current_paei_context.role.value} XP")
        
        elif r.get("action") == "finance_processed":
            summary.append("✅ Financial tasks processed")
            
        elif r.get("action") == "email_sent":
            summary.append("✅ Email sent successfully")
            
        elif r.get("action") == "calendar_event_created":
            summary.append("✅ Calendar event scheduled")
            
        elif r.get("status") == "error":
            summary.append("❌ Something went wrong")
            
        elif r.get("status") == "blocked":
            summary.append("⚠️ Need more information")
    
    if not summary:
        # Check parent decision for unified response
        decision = state.parent_decision or {}
        unified_response = decision.get("unified_response")
        if unified_response:
            state.final_response = unified_response
            return state
        summary.append("✅ Action completed successfully")
    
    # -------------------------------------------------
    # 3. LLM: USER-FACING RESPONSE
    # -------------------------------------------------
    # SPECIAL CASE: Rich research response
    if has_research and research_data:
        prompt = f"""
Generate a comprehensive, helpful research response to the user.

RESEARCH REQUEST: {research_data.get('query', 'your topic')}

KEY FINDINGS (from {research_data.get('sources_count', 0)} sources):
{research_data.get('preview', 'Research completed successfully.')}

Other actions completed:
{chr(10).join(f"- {s}" for s in summary) if summary else "No additional actions"}

Rules:
- Start with warm acknowledgment of their research request
- Summarize key findings in 1-2 clear paragraphs
- Mention source credibility and confidence
- Note that full report is saved to Notion Research database
- End with offer to explore further or answer questions
- Be professional, approachable, and slightly enthusiastic
- Use 1-2 relevant emojis naturally
- Keep it concise but informative (2-3 sentences)
"""
    else:
        # Standard prompt for other actions
        prompt = f"""
Generate a calm, warm, and professional response to the user.

Actions completed:
{chr(10).join(f"- {s}" for s in summary)}

Rules:
- Speak naturally, like a trusted friend and co-pilot
- Be encouraging and positive
- Acknowledge the specific action that was completed
- If XP was awarded, mention it positively
- Keep it concise and clear (1-2 sentences max)
- Never mention agents, tools, or internal systems
- Use emojis sparingly if appropriate
"""

    try:
        response = _llm_complete(prompt)
        state.final_response = response.strip()
    except Exception:
        logger.exception("LLM response generation failed")
        # Fallback response
        if has_research and research_data:
            # Special fallback for research
            state.final_response = (
                f"📚 Research completed on: {research_data.get('query', 'your topic')}\n\n"
                f"I found {research_data.get('sources_count', 0)} credible sources. "
                f"Key insights: {research_data.get('preview', 'Check Notion for full report.')}\n\n"
                f"✅ Full report saved to Notion Research database!"
            )
        elif summary:
            state.final_response = f"Done! {summary[0]}"
        else:
            state.final_response = "I've completed the requested action successfully."
    
    state.response_payload = {
        "status": "completed",
        "has_research": has_research,
        "summary": summary,
        "research_data": research_data if has_research else None
    }
    
    return state

def _generate_response_from_instructions(instructions: List[Dict], decision: Dict) -> str:
    """Generate response directly from instructions when no agent outputs"""
    
    # Count actions (excluding XP agent)
    action_agents = [i for i in instructions if i.get("agent") != "xp_agent"]
    
    if not action_agents:
        return "All set! Your request has been processed."
    
    # Get PAEI context
    paei_decision = decision.get("paei_decision", {})
    role = paei_decision.get("role", "P")
    xp_amount = paei_decision.get("xp_amount", 0)
    
    # Map agent to action type
    agent_map = {
        "task_agent": "task",
        "calendar_agent": "meeting/event",
        "email_agent": "email",
        "finance_agent": "financial task",
        "fireflies_agent": "meeting processing",
        "browser_agent": "research",
        "research_agent": "research synthesis",
        "weather_agent": "weather check"
    }
    
    action_types = []
    for instr in action_agents:
        agent = instr.get("agent")
        mapped = agent_map.get(agent, "action")
        if mapped not in action_types:
            action_types.append(mapped)
    
    if len(action_types) == 1:
        base = f"✅ {action_types[0].capitalize()} scheduled"
    else:
        base = f"✅ {len(action_types)} actions coordinated"
    
    # Add XP if awarded
    if xp_amount > 0:
        return f"{base}. +{xp_amount} {role} XP awarded!"
    
    return f"{base} successfully."