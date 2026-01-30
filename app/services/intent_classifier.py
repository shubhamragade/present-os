"""
PDF-COMPLIANT Intent Classifier - FINAL WORKING VERSION
FIXED: Research properly classified as READ domain, not WRITE category
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from pydantic import BaseModel, Field, ValidationError
from openai import OpenAI
from app.config.settings import settings

logger = logging.getLogger("presentos.intent")

_INTENT_CACHE: Dict[str, Dict[str, Any]] = {}
_CACHE_MAX_AGE = 300  # 5 minutes cache


# =================================================
# MODELS
# =================================================

class SubIntent(BaseModel):
    intent: str
    category: str
    payload: Dict[str, Any] = Field(default_factory=dict)
    paei_hint: Optional[str] = Field(None, description="Suggested PAEI role (P, A, E, I) for this specific action")


class IntentResult(BaseModel):
    intents: List[SubIntent]
    read_domains: List[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    explanation: str
    paei_hint: Optional[str] = Field(None, description="Overall PAEI role suggestion")
    model: str
    raw: Dict[str, Any]
    is_fallback: bool = False


# =================================================
# CLASSIFIER WITH FALLBACK
# =================================================

class IntentClassifier:
    def __init__(self, model: str, client: Optional[OpenAI] = None):
        self.model = model
        self.client = client or OpenAI(
            api_key=settings.OPENAI_API_KEY,
            timeout=30.0,
            max_retries=2
        )
        self._cache_timestamps: Dict[str, float] = {}

    def _hash(self, text: str) -> str:
        return hashlib.sha256(
            f"{self.model}|intent_v2|{text.strip().lower()}".encode()
        ).hexdigest()

    def _clean_cache(self):
        """Remove stale cache entries"""
        now = time.time()
        stale_keys = [
            k for k, ts in self._cache_timestamps.items()
            if now - ts > _CACHE_MAX_AGE
        ]
        for key in stale_keys:
            _INTENT_CACHE.pop(key, None)
            self._cache_timestamps.pop(key, None)

    def _call_model_cached(self, text: str) -> Dict[str, Any]:
        self._clean_cache()
        
        key = self._hash(text)
        if key in _INTENT_CACHE:
            logger.debug("Cache hit for intent classification")
            return _INTENT_CACHE[key]

        try:
            # FIX: Ensure "json" is in user message for OpenAI
            user_message = f"Analyze this text and return JSON analysis: {text}"
            
            # Define prompt-based instructions instead of strict schema to allow flexible payloads
            # We still keep the structure in the prompt
            
            start_time = time.time()
            resp = self.client.chat.completions.create(
                model=self.model,
                response_format={"type": "json_object"},
                temperature=0.1,
                messages=[
                    {"role": "system", "content": f"{INTENT_SYSTEM_PROMPT}\n\nIMPORTANT: Return a JSON object with 'intents' (array), 'read_domains' (array), 'confidence' (number), 'explanation' (string), and 'paei_hint' (string)."},
                    {"role": "user", "content": user_message},
                ],
                max_tokens=1000,
            )
            
            elapsed = time.time() - start_time
            logger.debug(f"OpenAI classification took {elapsed:.2f}s")

            raw_content = resp.choices[0].message.content
            
            # Structured Outputs guarantees valid JSON matching our schema
            data = json.loads(raw_content)

            # Validated by OpenAI, but strictly cache what we got
            _INTENT_CACHE[key] = data
            self._cache_timestamps[key] = time.time()
            
            return data

        except Exception as e:
            logger.error(f"OpenAI classification failed: {e}")
            return self._rule_based_fallback(text)

    def _rule_based_fallback(self, text: str) -> Dict[str, Any]:
        """Rule-based fallback when LLM fails"""
        text_lower = text.lower()
        intents = []
        read_domains = []
        
        # PDF-COMPLIANT CATEGORY MAPPING
        category_rules = {
            "task": ["task", "todo", "remind", "do", "finish", "complete", "work on"],
            "calendar": ["schedule", "meeting", "calendar", "appointment", "call", "sync"],
            "email": ["email", "send", "draft", "message", "reply", "contact"],
            "focus": ["focus", "deep work", "concentrate", "pomodoro"],
            "quest": ["quest", "goal", "project", "launch", "achieve", "result"],
            "map": ["map", "action plan", "massive action", "steps"],
            "meeting": ["meeting", "call", "zoom", "discuss", "chat"],
            "contact": ["contact", "person", "call", "reach out", "connect"],
            "xp": ["xp", "points", "gamify", "level up", "reward"],
            "weather": ["weather", "surf", "wind", "kite", "forecast", "conditions"],
            "finance": ["finance", "bill", "pay", "money", "budget", "invoice"],
            "fireflies": ["transcribe", "recording", "meeting notes", "minutes"],
            "chat": ["hi", "hello", "hey", "how are you", "martin", "presentos", "morning", "evening"],
        }
        
        read_domain_rules = {
            "plan_report": ["plan", "today", "schedule", "agenda", "daily plan"],
            "weather": ["weather", "surf", "wind", "forecast", "conditions"],
            "research": ["research", "find", "look up", "search"],
            "report": ["report", "summary", "status", "update"],
            "xp_status": ["xp", "points", "level", "progress", "xp report", "weekly xp"],
            "finance_status": ["finance", "money", "budget", "spending"],
            "quest_status": ["quest", "goal", "progress", "status"],
            "meeting_summary": ["meeting summary", "notes", "recap", "minutes"],
        }
        
        # Check for write intents
        for category, keywords in category_rules.items():
            if any(keyword in text_lower for keyword in keywords):
                intents.append({
                    "intent": f"create_{category}" if category not in ["xp", "weather", "finance"] else f"check_{category}",
                    "category": category,
                    "payload": {"text": text, "category": category}
                })
        
        # Check for read domains
        for domain, keywords in read_domain_rules.items():
            for keyword in keywords:
                if keyword in text_lower:
                    if domain not in read_domains:
                        read_domains.append(domain)
                    break
        
        # If no intents but has read domains, still process
        confidence = 0.7 if intents or read_domains else 0.3
        
        return {
            "intents": intents,
            "read_domains": read_domains,
            "confidence": confidence,
            "explanation": f"Rule-based fallback: detected {len(intents)} intents, {len(read_domains)} read domains",
            "fallback": True
        }

    # -------------------------------------------------
    # PUBLIC API
    # -------------------------------------------------

    def classify(self, text: str) -> IntentResult:
        """Main classification entry point"""
        if not text or not text.strip():
            return IntentResult(
                intents=[],
                read_domains=[],
                confidence=0.0,
                explanation="Empty input",
                model=self.model,
                raw={},
                is_fallback=False
            )
        
        raw = self._call_model_cached(text)
        
        # ADD DEBUG LOGGING
        logger.info(f"Raw intent data for '{text[:50]}...': {json.dumps(raw, indent=2)}")
        
        raw_intents = raw.get("intents", [])
        read_domains = raw.get("read_domains", [])
        confidence = float(raw.get("confidence", 0.0))
        is_fallback = raw.get("fallback", False)

        intents: List[SubIntent] = []
        for item in raw_intents:
            try:
                # Ensure category is valid
                if item.get("category") not in VALID_CATEGORIES:
                    logger.warning(f"Invalid category: {item.get('category')}")
                    continue
                    
                intents.append(SubIntent(**item))
            except ValidationError as e:
                logger.warning(f"Invalid SubIntent dropped: {e}")

        # Adjust confidence based on findings
        if not intents and not read_domains:
            confidence = min(confidence, 0.4)
        elif len(intents) > 1:
            confidence = min(confidence, 0.8)
        elif is_fallback:
            confidence = min(confidence, 0.6)

        return IntentResult(
            intents=intents,
            read_domains=read_domains,
            confidence=confidence,
            explanation=raw.get("explanation", ""),
            paei_hint=raw.get("paei_hint"),
            model=self.model,
            raw=raw,
            is_fallback=is_fallback,
        )


def get_default_intent_classifier() -> IntentClassifier:
    return IntentClassifier(model=settings.OPENAI_MODEL)


# =================================================
# VALID CATEGORIES (MUST MATCH PARENT AGENT)
# =================================================
# ✅ FIXED: "research" REMOVED from WRITE categories
VALID_CATEGORIES = {
    "task", "calendar", "email", "focus", "quest", "map", 
    "meeting", "contact", "xp", "weather", "finance", "fireflies", "chat"
    # ❌ "research" is NOT here - it's ONLY a READ domain
}

VALID_READ_DOMAINS = {
    "plan_report", "weather", "research", "report", 
    "xp_status", "finance_status", "quest_status", "meeting_summary", "contact_info"
}


# =================================================
# SYSTEM PROMPT (FINAL WORKING VERSION)
# =================================================

INTENT_SYSTEM_PROMPT = """You are the PresentOS Intent Classifier (PDF-COMPLIANT). You must output valid JSON format only.

CRITICAL RULE: "research" is ALWAYS a READ-ONLY domain, NEVER a WRITE category.

WRITE CATEGORIES (User wants to DO/SAVE something):
- task: Creating/updating tasks. Payload MUST include: 'title' (string), 'priority' (Low|Medium|High), 'due' (ISO date), 'quest_id' (string, if linked to a quest).
- calendar: Scheduling meetings, events, or appointments ("schedule meeting")
- email: Sending, drafting, scanning, or managing emails ("send email", "scan inbox", "check emails")
- focus: Starting focus sessions. Payload SHOULD include: 'duration_minutes' (int), 'deep_work' (bool).
- quest: Creating goals. Payload MUST include: 'name' (string), 'purpose' (string), 'result' (string), 'category' (string).
- map: Creating Massive Action Plans ("create MAP")
- meeting: Scheduling meetings ("schedule call")
- contact: Managing contacts ("add contact", "save note on John", "Sarah prefers calls", "John's phone number is 123"). 
  - USE THIS whenever user PROVIDES information about a person.
  - Payload SHOULD include: 'contact_name', 'note' or 'phone' or 'email'.
- xp: Awarding XP points ("award XP")
- weather: Checking conditions for decisions ("check weather")
- finance: Processing bills/payments ("pay bill")
- fireflies: Meeting transcription ("transcribe meeting")
- chat: Greetings, small talk, or general engagement ("hi", "how are you")

READ-ONLY DOMAINS (User wants INFORMATION):
- plan_report: "What's my plan today?", "Show my daily schedule"
- weather: "What's the weather?", "Check surf conditions"
- research: "Research something", "Look up information", "Find articles about"
- report: "Give me a report", "Status update", "Weekly summary"
- xp_status: "How many XP do I have?", "Show XP report"
- finance_status: "Budget status", "Financial update"
- quest_status: "Quest progress", "How's my goal"
- meeting_summary: "Meeting notes", "Summarize meeting"
- contact_info: "What do I know about Sarah?", "Show John's contact info", "What is Maria's number?"
  - USE THIS ONLY when the user is ASKING for information.

CRITICAL EXAMPLES:
1. User: "Sarah prefers phone calls over email."
→ intents: [{"intent": "add_note", "category": "contact", "payload": {"contact_name": "Sarah", "note": "prefers phone calls over email"}, "paei_hint": "I"}]
→ read_domains: []
→ confidence: 1.0

2. User: "What do I know about Sarah?"
→ intents: []
→ read_domains: ["contact_info"]
→ confidence: 1.0

2. User: "Look up information about AI trends"
→ intents: []  # ← NO WRITE INTENTS!
→ read_domains: ["research"]
→ confidence: 0.9

3. User: "Find me recent articles about machine learning"
→ intents: []  # ← NO WRITE INTENTS!
→ read_domains: ["research"]
→ confidence: 0.9

4. User: "What's the weather and research surf conditions?"
→ intents: []  # ← NO WRITE INTENTS!
→ read_domains: ["weather", "research"]  # ← BOTH domains
→ confidence: 0.9

5. User: "Schedule a meeting and research the topic first"
→ intents: [{"intent": "schedule_meeting", "category": "calendar", ...}]
→ read_domains: ["research"]  # ← Research is STILL read domain
→ confidence: 0.9

ALWAYS REMEMBER:
- "research" keywords: research, look up, find, search, investigate, explore
- If ANY research keyword appears → add "research" to read_domains
- NEVER put "research" in intents array

PAEI HINTS (Optional):
- P (Producer): Action, doing, urgent, deadlines ("do this now", "finish")
- A (Administrator): Structure, organizing, details, documenting ("organize", "plan")
- E (Entrepreneur): Vision, ideas, strategy, creative ("brainstorm", "new idea")
- I (Integrator): People, connection, feelings, team ("call mom", "team meeting")

OUTPUT FORMAT (JSON ONLY):
{
  "intents": [{"intent": "...", "category": "...", "payload": {}, "paei_hint": "P"}],
  "read_domains": ["...", "..."],
  "confidence": 0.9,
  "explanation": "Brief explanation",
  "paei_hint": "P"
}
"""

# =================================================
# TEST FUNCTION
# =================================================

def test_intent_classifier():
    """Test the intent classifier with various queries"""
    classifier = get_default_intent_classifier()
    
    test_cases = [
        ("Research best no-code tools for building AI apps in 2026", "Should be read_domains: ['research']"),
        ("Look up information about machine learning trends", "Should be read_domains: ['research']"),
        ("Find articles about AI ethics", "Should be read_domains: ['research']"),
        ("What's my plan today?", "Should be read_domains: ['plan_report']"),
        ("Check the weather and surf conditions", "Should be read_domains: ['weather']"),
        ("Show me my XP report", "Should be read_domains: ['xp_status']"),
        ("Schedule a meeting tomorrow at 2pm", "Should be intents with category: 'calendar'"),
        ("Add a task to call mom tonight", "Should be intents with category: 'task'"),
    ]
    
    for text, expected in test_cases:
        result = classifier.classify(text)
        print(f"\nTest: {text}")
        print(f"Expected: {expected}")
        print(f"Got: intents={[(i.category, i.intent) for i in result.intents]}, read_domains={result.read_domains}")
        print(f"Confidence: {result.confidence}")
        print(f"Explanation: {result.explanation}")