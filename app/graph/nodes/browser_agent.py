"""
Browser Agent - PDF COMPLIANT (Pages 28-29)
Using ONLY Perplexity API from your .env
"""

from __future__ import annotations
import os
import logging
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

import requests
from tenacity import retry, stop_after_attempt, wait_exponential

from app.graph.state import PresentOSState
from app.integrations.notion_client import NotionClient
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.browser_agent")

# ONLY using Perplexity from your .env
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PPLX_URL = "https://api.perplexity.ai/chat/completions"

# PDF Page 29: Research types
RESEARCH_TYPES = {
    "competitive_analysis": "Analyze competitors and extract key features",
    "content_curation": "Find recent articles and summarize key points",
    "price_monitoring": "Check current prices and deals",
    "market_research": "What are people saying on social media/forums",
    "general_research": "General web search and information gathering"
}


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
def _perplexity_search(
    query: str,
    research_type: str = "general_research",
    detailed: bool = False
) -> Dict[str, Any]:
    """
    PDF Page 28-29: Use Perplexity for web search with citations
    
    Returns: {
        "answer": str,
        "citations": List[Dict],
        "sources": List[str],
        "search_summary": str
    }
    """
    if not PERPLEXITY_API_KEY:
        logger.error("PERPLEXITY_API_KEY missing from .env")
        return {
            "error": "PERPLEXITY_API_KEY missing. Add to .env: PERPLEXITY_API_KEY=your_key",
            "answer": "",
            "citations": [],
            "sources": []
        }
    
    # PDF Page 29: Different prompts for different research types
    system_prompts = {
        "competitive_analysis": """You are a competitive intelligence analyst. 
        Analyze competitors and extract:
        1. Key features and differentiators
        2. Pricing information if available
        3. Strengths and weaknesses
        4. Market positioning
        Include specific citations with URLs.""",
        
        "content_curation": """You are a content curator. Find and summarize:
        1. Recent articles (last 6 months preferred)
        2. Key insights and takeaways
        3. Author credibility
        4. Actionable insights
        Include citations with publication dates.""",
        
        "price_monitoring": """You are a price monitoring agent. Find:
        1. Current prices and any discounts
        2. Price history trends if available
        3. Best deals currently available
        4. Retailer comparisons
        Never scrape behind paywalls (PDF requirement).""",
        
        "market_research": """You are a market researcher. Analyze:
        1. Sentiment on social media/forums
        2. Common pain points
        3. Emerging trends
        4. Customer feedback
        Cite specific forum posts or social media when possible.""",
        
        "general_research": """You are a research assistant. Provide:
        1. Accurate, up-to-date information
        2. Multiple perspectives
        3. Credible sources
        4. Clear citations
        Respect robots.txt and rate limits."""
    }
    
    system_prompt = system_prompts.get(research_type, system_prompts["general_research"])
    
    payload = {
        "model": "sonar-pro",
        "messages": [
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": query + (" Please provide detailed analysis with citations." if detailed else "")
            }
        ],
        "temperature": 0.2,
        "max_tokens": 2000 if detailed else 1000,
        "return_citations": True  # PDF: Cites all sources properly
    }
    
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json",
    }
    
    try:
        resp = requests.post(PPLX_URL, json=payload, headers=headers, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        answer = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])
        
        # Extract sources from citations
        sources = []
        for citation in citations:
            if isinstance(citation, dict) and citation.get("url"):
                sources.append({
                    "url": citation.get("url"),
                    "title": citation.get("title", "Source"),
                    "date": citation.get("date", ""),
                    "snippet": citation.get("snippet", "")[:200]
                })
        
        return {
            "success": True,
            "answer": answer,
            "citations": citations,
            "sources": sources[:10],  # Limit to 10 sources
            "research_type": research_type,
            "query": query,
            "model": "sonar-pro"
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Perplexity API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "answer": "",
            "citations": [],
            "sources": []
        }


def _save_to_notion(
    notion: NotionClient,
    query: str,
    result: Dict[str, Any],
    quest_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    PDF Page 29: "Results saved to Notion 'Research' database"
    
    Creates a research page in Notion with:
    - Query and answer
    - Sources and citations
    - Links to Quest if provided
    """
    try:
        # Check if we have a research database
        if not hasattr(notion, 'db_ids') or 'research' not in notion.db_ids:
            logger.warning("No research database configured in Notion")
            return {"success": False, "error": "No research database"}
        
        # Build research properties matching your schema
        props = {
            "Name": notion._prop_title(f"Research: {query[:50]}..."),
            "Query": notion._prop_text(query),
            "Answer": notion._prop_text(result.get("answer", "")[:2000]),
            "Research Type": notion._prop_select(result.get("research_type", "general_research")),
            "Sources Count": notion._prop_number(len(result.get("sources", []))),
            "Status": notion._prop_select("Completed"),
            "Date": notion._prop_date(datetime.now().isoformat()),
            "Source": notion._prop_select("Browser Agent")
        }
        
        # Link to Quest if provided (PDF: Links to Quest)
        if quest_id:
            props["Quest"] = notion._prop_relation([quest_id])
        
        # Add sources as rich text
        sources_text = "Sources:\n\n"
        for i, source in enumerate(result.get("sources", [])[:5]):
            sources_text += f"{i+1}. {source.get('title', 'Source')}\n"
            if source.get('url'):
                sources_text += f"   URL: {source['url']}\n"
            if source.get('snippet'):
                sources_text += f"   Excerpt: {source['snippet']}\n"
            sources_text += "\n"
        
        props["Sources"] = notion._prop_text(sources_text[:2000])
        
        # Create page in research database
        body = {
            "parent": {"database_id": notion.db_ids["research"]},
            "properties": props
        }
        
        res = notion._request("POST", "/pages", json_body=body)
        
        logger.info(f"✅ Research saved to Notion: {res.get('id')}")
        return {
            "success": True,
            "page_id": res.get("id"),
            "url": res.get("url")
        }
        
    except Exception as e:
        logger.error(f"Failed to save research to Notion: {e}")
        return {"success": False, "error": str(e)}


def _determine_research_type(query: str) -> str:
    """Determine research type based on query content"""
    query_lower = query.lower()
    
    if any(word in query_lower for word in ["competitor", "competitive", "vs ", "compare", "alternative"]):
        return "competitive_analysis"
    elif any(word in query_lower for word in ["article", "blog", "news", "recent", "trend"]):
        return "content_curation"
    elif any(word in query_lower for word in ["price", "cost", "$", "deal", "sale", "discount"]):
        return "price_monitoring"
    elif any(word in query_lower for word in ["reddit", "twitter", "forum", "people saying", "sentiment"]):
        return "market_research"
    else:
        return "general_research"


def run_browser_node(state: PresentOSState) -> PresentOSState:
    """
    Browser Agent - PDF COMPLIANT using only Perplexity API
    
    PDF Page 28: "Automates information gathering so users stay in creative flow"
    """
    
    instruction = get_instruction(state, "browser_agent")
    if not instruction:
        return state
    
    query = instruction.get("query")
    quest_id = instruction.get("quest_id")  # PDF: Links to Quest
    
    if not query:
        state.add_agent_output(
            agent="browser_agent",
            result={"status": "ignored", "reason": "no_query"},
            score=0.0
        )
        return state
    
    try:
        # PDF: Determine research type
        research_type = _determine_research_type(query)
        logger.info(f"BrowserAgent → {research_type}: {query}")
        
        # Perform search with Perplexity
        result = _perplexity_search(query, research_type, detailed=True)
        
        # PDF: Save to Notion if successful
        if result.get("success"):
            notion = NotionClient()
            saved = _save_to_notion(notion, query, result, quest_id)
            result["notion_saved"] = saved
            
            # PDF: "Can be scheduled automatically"
            if instruction.get("schedule_weekly"):
                state.planned_actions.append({
                    "type": "schedule_research",
                    "query": query,
                    "frequency": "weekly",
                    "research_type": research_type,
                    "quest_id": quest_id
                })
        
        # Agent output
        state.add_agent_output(
            agent="browser_agent",
            result={
                "action": "search_completed",
                "research_type": research_type,
                "query": query,
                "result": {
                    "answer": result.get("answer", "")[:500] + "..." if len(result.get("answer", "")) > 500 else result.get("answer", ""),
                    "sources_count": len(result.get("sources", [])),
                    "success": result.get("success", False),
                    "notion_saved": result.get("notion_saved", {}).get("success", False)
                },
                "quest_id": quest_id,
                "full_result": result if state.config.get("debug_mode") else None
            },
            score=0.8 if result.get("success") else 0.3
        )
        
        # PDF: "Preserves flow state for creative work"
        # Set state to indicate research is available
        state.research_available = True
        
        return state
        
    except Exception as e:
        logger.exception(f"BrowserAgent failed: {e}")
        state.add_agent_output(
            agent="browser_agent",
            result={
                "status": "error",
                "error": str(e),
                "query": query
            },
            score=0.0
        )
        return state