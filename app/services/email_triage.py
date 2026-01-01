# app/services/email_triage.py

from __future__ import annotations
from typing import Dict, Any
import json
from openai import OpenAI

client = OpenAI()

SYSTEM_PROMPT = """
You are the Email Intelligence Agent for PresentOS.

Your job:
- Analyze an incoming email
- Decide what action is required
- Think semantically (NOT keywords)
- Use tone, intent, urgency, and context
- Apply the PAEI model

STRICT RULES:
- NEVER send emails
- NEVER auto-approve actions
- NEVER hallucinate facts
- If response is needed → create DRAFT TEXT ONLY
- Output MUST be valid JSON (no markdown, no comments)

PAEI GUIDANCE:
P = urgent execution, action required now
A = administrative, routine, compliance, bills
E = entrepreneurial, client growth, opportunity
I = integrator, people, emotions, relationships

Return EXACTLY this JSON schema:

{
  "actionable": true|false,
  "category": "bill|client|internal|meeting|info|other",
  "priority": "P1|P2|P3|P4",
  "paei": "P|A|E|I",
  "needs_response": true|false,
  "needs_calendar": true|false,
  "needs_task": true|false,
  "draft_reply": string|null,
  "summary": string,
  "confidence": number
}
"""

def triage_email(email: Dict[str, Any]) -> Dict[str, Any]:
    content = f"""
FROM: {email.get("from")}
SUBJECT: {email.get("subject")}
BODY:
{email.get("body")}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content},
        ],
        temperature=0.2,
    )

    raw = response.choices[0].message.content

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        # Hard fail-safe (never crash pipeline)
        return {
            "actionable": False,
            "category": "other",
            "priority": "P4",
            "paei": "A",
            "needs_response": False,
            "needs_calendar": False,
            "needs_task": False,
            "draft_reply": None,
            "summary": "Unable to confidently interpret email.",
            "confidence": 0.1,
        }

    return parsed
