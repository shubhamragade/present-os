from __future__ import annotations
from typing import Dict, Any, List
import json
from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
You are a meeting intelligence engine for an AI operating system.

Your job:
- Analyze a completed meeting transcript or summary
- Extract decisions, action items, follow-ups, and risks
- Think semantically, not by keywords
- Be conservative (do not invent actions)

STRICT RULES:
- Output VALID JSON only
- No markdown
- No hallucination
- Short, factual phrasing

OUTPUT SCHEMA:
{
  "summary": string,
  "decisions": [string],
  "action_items": [
    { "task": string, "owner": string|null, "urgency": "low|medium|high" }
  ],
  "follow_ups": [
    { "type": "email|message", "target": string, "reason": string }
  ],
  "risks": [string],
  "confidence": number
}
"""

def analyze_meeting(meeting: Dict[str, Any]) -> Dict[str, Any]:
    content = f"""
TITLE: {meeting.get("title")}
TRANSCRIPT:
{meeting.get("transcript")}
SUMMARY:
{meeting.get("summary")}
"""

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.2,
    )

    raw = resp.choices[0].message.content

    try:
        return json.loads(raw)
    except Exception:
        return {
            "summary": "Unable to confidently analyze meeting.",
            "decisions": [],
            "action_items": [],
            "follow_ups": [],
            "risks": [],
            "confidence": 0.2,
        }
