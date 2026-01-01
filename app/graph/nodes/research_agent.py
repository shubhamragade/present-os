"""
Research Agent - PDF COMPLIANT (Pages 29-30)

PDF Requirements:
✅ Synthesizes BrowserAgent output
✅ Creates structured insights
✅ Generates Notion reports
✅ Never browses the web directly
✅ Works with your existing Notion schema
"""

from __future__ import annotations
import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

import requests

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient

logger = logging.getLogger("presentos.research_agent")

# Use OpenAI from your .env for synthesis
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


def run_research_node(state: PresentOSState) -> PresentOSState:
    """
    Research Agent - Synthesizes BrowserAgent output into structured insights
    
    PDF Page 29: "Provides weekly/monthly insights to optimize life"
    """
    
    # Get latest BrowserAgent output
    browser_outputs = [
        o for o in state.agent_outputs
        if o.agent_name == "browser_agent" and o.result.get("action") == "search_completed"
    ]
    
    if not browser_outputs:
        logger.info("ResearchAgent: No browser output available")
        state.add_agent_output(
            agent="research_agent",
            result={"status": "ignored", "reason": "no_browser_data"},
            score=0.0
        )
        return state
    
    # Get the most recent completed search
    latest_output = browser_outputs[-1]
    result_data = latest_output.result
    
    query = result_data.get("query")
    browser_result = result_data.get("result", {})
    full_result = result_data.get("full_result", {})
    quest_id = result_data.get("quest_id")
    
    if not browser_result.get("success"):
        state.add_agent_output(
            agent="research_agent",
            result={
                "status": "error",
                "reason": "browser_search_failed",
                "query": query
            },
            score=0.0
        )
        return state
    
    try:
        # PDF: Generate structured insights
        insights = _generate_structured_insights(full_result, query)
        
        # PDF: Create research report in Notion
        notion = NotionClient()
        report_saved = _create_research_report(notion, query, insights, quest_id)
        
        # PDF: Generate summary for Martin/Telegram
        summary = _generate_executive_summary(insights)
        
        # Agent output
        state.add_agent_output(
            agent="research_agent",
            result={
                "action": "research_synthesized",
                "query": query,
                "insights": {
                    "key_points": insights.get("key_points", [])[:3],
                    "recommendations": insights.get("recommendations", [])[:3],
                    "confidence": insights.get("confidence", 0.7),
                    "summary": summary
                },
                "notion_report_created": report_saved.get("success", False),
                "report_url": report_saved.get("url"),
                "quest_id": quest_id
            },
            score=insights.get("confidence", 0.7)
        )
        
        # PDF: "Can be scheduled automatically (e.g., weekly competitor monitoring)"
        if result_data.get("research_type") == "competitive_analysis":
            state.planned_actions.append({
                "type": "schedule_competitive_monitoring",
                "query": query,
                "frequency": "weekly",
                "next_run": (datetime.now().timestamp() + 604800)  # 7 days
            })
        
        logger.info(f"ResearchAgent completed synthesis for: {query}")
        return state
        
    except Exception as e:
        logger.exception(f"ResearchAgent failed: {e}")
        state.add_agent_output(
            agent="research_agent",
            result={
                "status": "error",
                "error": str(e),
                "query": query
            },
            score=0.0
        )
        return state


def _generate_structured_insights(full_result: Dict[str, Any], query: str) -> Dict[str, Any]:
    """
    PDF: Generate structured insights from research
    
    Uses OpenAI to synthesize if available, otherwise uses heuristic methods
    """
    
    answer = full_result.get("answer", "")
    sources = full_result.get("sources", [])
    research_type = full_result.get("research_type", "general_research")
    
    # Use OpenAI for better synthesis if available
    if OPENAI_API_KEY:
        return _synthesize_with_openai(answer, sources, query, research_type)
    else:
        # Heuristic synthesis
        return _synthesize_heuristic(answer, sources, research_type)


def _synthesize_with_openai(
    answer: str,
    sources: List[Dict],
    query: str,
    research_type: str
) -> Dict[str, Any]:
    """Use OpenAI to synthesize research into structured insights"""
    
    try:
        system_prompt = f"""You are a research synthesis expert. Analyze this research and provide:

1. **KEY POINTS** (3-5 bullet points of most important findings)
2. **RECOMMENDATIONS** (3 actionable recommendations based on findings)
3. **CONFIDENCE SCORE** (0.1 to 1.0 based on source quality and recency)
4. **EXECUTIVE SUMMARY** (2-3 sentence summary for busy executives)

Research Type: {research_type}
Query: {query}
Number of Sources: {len(sources)}

Format your response as JSON:
{{
    "key_points": ["point1", "point2", ...],
    "recommendations": ["rec1", "rec2", ...],
    "confidence": 0.85,
    "executive_summary": "summary here"
}}"""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Research Answer:\n{answer[:3000]}"}
        ]
        
        if sources:
            sources_text = "\nSources:\n" + "\n".join([
                f"- {s.get('title', 'Source')}: {s.get('snippet', '')[:100]}"
                for s in sources[:5]
            ])
            messages[1]["content"] += sources_text
        
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                "messages": messages,
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        insights_json = data["choices"][0]["message"]["content"]
        
        return json.loads(insights_json)
        
    except Exception as e:
        logger.error(f"OpenAI synthesis failed: {e}, using heuristic")
        return _synthesize_heuristic(answer, sources, research_type)


def _synthesize_heuristic(
    answer: str,
    sources: List[Dict],
    research_type: str
) -> Dict[str, Any]:
    """Heuristic synthesis without OpenAI"""
    
    lines = [line.strip() for line in answer.split('\n') if line.strip()]
    
    # Extract key points (lines that look important)
    key_points = []
    for line in lines:
        if len(line) > 30 and len(line) < 200:
            if any(marker in line.lower() for marker in ["important", "key", "critical", "essential", "major"]):
                key_points.append(line)
            elif line[0].isupper() and line[-1] in '.!?' and len(key_points) < 5:
                key_points.append(line)
    
    # Generate recommendations based on research type
    recommendations = []
    if research_type == "competitive_analysis":
        recommendations = [
            "Monitor competitor pricing monthly",
            "Differentiate on unique features",
            "Consider strategic partnerships"
        ]
    elif research_type == "content_curation":
        recommendations = [
            "Create summary of key insights",
            "Share findings with team",
            "Schedule follow-up research in 30 days"
        ]
    elif research_type == "price_monitoring":
        recommendations = [
            "Set price alerts for changes",
            "Consider buying during sales",
            "Compare across multiple retailers"
        ]
    else:
        recommendations = [
            "Document findings for future reference",
            "Share insights with relevant stakeholders",
            "Schedule follow-up if needed"
        ]
    
    # Calculate confidence based on sources
    confidence = 0.5
    if len(sources) >= 3:
        confidence = 0.7
    if len(sources) >= 5:
        confidence = 0.8
    
    recent_sources = sum(1 for s in sources if "2024" in str(s.get("date", "")) or "2025" in str(s.get("date", "")))
    if recent_sources >= 2:
        confidence = min(confidence + 0.1, 0.9)
    
    return {
        "key_points": key_points[:5],
        "recommendations": recommendations,
        "confidence": confidence,
        "executive_summary": f"Research on {research_type.replace('_', ' ')} completed with {len(sources)} sources."
    }


def _create_research_report(
    notion: NotionClient,
    query: str,
    insights: Dict[str, Any],
    quest_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    PDF Page 29: "Creates Notion page: 'Research Summary'"
    """
    try:
        # Use research database or fall back to tasks
        db_id = notion.db_ids.get("research") or notion.db_ids.get("tasks")
        
        if not db_id:
            return {"success": False, "error": "No database available"}
        
        # Build report properties
        props = {
            "Name": notion._prop_title(f"Research Report: {query[:40]}..."),
            "Query": notion._prop_text(query),
            "Status": notion._prop_select("Completed"),
            "Type": notion._prop_select("Research Report"),
            "Confidence Score": notion._prop_number(insights.get("confidence", 0.7)),
            "Date": notion._prop_date(datetime.now().isoformat()),
            "Source": notion._prop_select("Research Agent")
        }
        
        # Link to Quest if provided
        if quest_id:
            props["Quest"] = notion._prop_relation([quest_id])
        
        # Add insights as rich text
        insights_text = f"# Research Insights\n\n"
        insights_text += f"## Key Points\n"
        for i, point in enumerate(insights.get("key_points", [])[:5], 1):
            insights_text += f"{i}. {point}\n"
        
        insights_text += f"\n## Recommendations\n"
        for i, rec in enumerate(insights.get("recommendations", [])[:3], 1):
            insights_text += f"{i}. {rec}\n"
        
        insights_text += f"\n## Executive Summary\n{insights.get('executive_summary', '')}"
        
        props["Insights"] = notion._prop_text(insights_text[:4000])
        
        # Create report page
        body = {
            "parent": {"database_id": db_id},
            "properties": props
        }
        
        res = notion._request("POST", "/pages", json_body=body)
        
        logger.info(f"✅ Research report created in Notion: {res.get('id')}")
        return {
            "success": True,
            "page_id": res.get("id"),
            "url": res.get("url")
        }
        
    except Exception as e:
        logger.error(f"Failed to create research report: {e}")
        return {"success": False, "error": str(e)}


def _generate_executive_summary(insights: Dict[str, Any]) -> str:
    """Generate 2-3 sentence executive summary"""
    key_points = insights.get("key_points", [])
    recommendations = insights.get("recommendations", [])
    confidence = insights.get("confidence", 0.7)
    
    if key_points:
        summary = f"Research identified {len(key_points)} key insights"
        if recommendations:
            summary += f" and {len(recommendations)} actionable recommendations"
        summary += f". Confidence score: {confidence:.1%}."
        
        if confidence > 0.8:
            summary += " Findings are highly reliable."
        elif confidence > 0.6:
            summary += " Findings are reasonably reliable."
        else:
            summary += " Additional verification recommended."
        
        return summary
    
    return "Research completed. Review detailed findings for specific insights."