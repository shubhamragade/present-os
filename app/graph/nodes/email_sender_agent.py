# app/graph/nodes/email_sender_agent.py - FIXED VERSION

from __future__ import annotations
import logging
import random
from typing import Dict, Any, List
from datetime import datetime, timedelta

from app.graph.state import PresentOSState
from app.integrations.gmail_client import create_draft
from app.integrations.gmail_client import search_emails
from app.utils.instruction_utils import get_instruction
from app.graph.nodes.contact_agent import run_contact_node
from app.services.rag_service import get_rag_service

logger = logging.getLogger("presentos.email_sender")


def run_email_sender_node(state: PresentOSState) -> PresentOSState:
    """
    Email Sender Agent (EXECUTION + SMART CHECK)
    
    Now uses your actual RAG service for:
    1. Looking up contact memories
    2. Checking communication patterns
    3. Learning preferences
    4. Making intelligent sending decisions
    """
    if "email_sender_agent" not in state.activated_agents:
        return state
    
    instruction = get_instruction(state, "email_sender_agent")
    if not instruction:
        return state

    email_ctx = instruction.get("email_context", {})
    contact_name = instruction.get("contact_name")
    contact_email = instruction.get("contact_email")
    
    if not email_ctx or (not contact_name and not contact_email):
        state.add_agent_output(
            agent="email_sender_agent",
            result={"status": "ignored", "reason": "missing_context"},
            score=0.0,
        )
        return state

    try:
        # ===== STEP 1: GET CONTACT FROM NOTION =====
        contact_info = get_contact_from_notion(state, contact_name, contact_email)
        if not contact_info:
            return state  # Error already logged
        
        # ===== STEP 2: CHECK LAST EMAIL SENT =====
        last_email_info = check_last_email_sent(contact_info["email"])
        
        # ===== STEP 3: USE YOUR RAG SERVICE =====
        rag_service = get_rag_service()
        
        # Query RAG for contact memories
        contact_memories = get_contact_memories(rag_service, contact_info)
        
        # Query RAG for topic context
        topic_memories = get_topic_memories(rag_service, email_ctx, contact_info)
        
        rag_context = {
            "contact_memories": contact_memories,
            "topic_memories": topic_memories,
        }
        
        # ===== STEP 4: DECIDE IF WE SHOULD SEND =====
        should_send, reason = decide_if_should_send(
            contact_info, 
            last_email_info, 
            email_ctx,
            rag_context
        )
        
        if not should_send:
            state.add_agent_output(
                agent="email_sender_agent",
                result={
                    "status": "skipped",
                    "reason": reason,
                    "last_email_sent": last_email_info.get("date"),
                    "days_since": last_email_info.get("days_since"),
                    "rag_memories_found": len(contact_memories) + len(topic_memories),
                },
                score=0.3,
            )
            return state
        
        # ===== STEP 5: CREATE PERSONALIZED EMAIL =====
        personalized_email = create_personalized_email(
            email_ctx, 
            contact_info, 
            rag_context,
            last_email_info
        )
        
        # ===== STEP 6: SEND DRAFT =====
        draft = create_draft(
            to=contact_info["email"],
            subject=personalized_email["subject"],
            body=personalized_email["body"],
            thread_id=email_ctx.get("thread_id"),
        )
        
        # ===== STEP 7: STORE THIS EMAIL IN RAG MEMORY =====
        store_email_memory(rag_service, contact_info, personalized_email, draft, reason)
        
        # ===== STEP 8: LOG XP =====
        state.planned_actions.append({
            "type": "xp_event",
            "paei": email_ctx.get("paei"),
            "reason": "email_draft_created",
            "email_id": email_ctx.get("email_id"),
            "contact_id": contact_info["id"],
            "tone_used": personalized_email["tone"],
            "last_email_checked": last_email_info.get("date"),
            "rag_memories_used": len(contact_memories) + len(topic_memories),
            "decision_reason": reason,
        })
        
        state.add_agent_output(
            agent="email_sender_agent",
            result={
                "status": "draft_created",
                "draft_id": draft.get("id"),
                "to": contact_info["email"],
                "contact_name": contact_info["name"],
                "tone_applied": personalized_email["tone"],
                "last_email_checked": last_email_info.get("date"),
                "rag_memories_used": len(contact_memories) + len(topic_memories),
                "decision_reason": reason,
                "email_preview": personalized_email["body"][:200] + "...",
            },
            score=0.95,
        )
        
        return state
        
    except Exception as e:
        logger.exception("EmailSenderAgent failed")
        state.add_agent_output(
            agent="email_sender_agent",
            result={"status": "error", "error": str(e)},
            score=0.0,
        )
        return state


# ===== HELPER FUNCTIONS =====

def get_contact_from_notion(state: PresentOSState, name: str, email: str) -> Dict:
    """Get contact info from Notion via Contact Agent"""
    temp_state = state.copy()
    temp_state.activated_agents.add("contact_agent")
    temp_state.instructions["contact_agent"] = {
        "contact_name": name,
        "contact_email": email
    }
    
    temp_state = run_contact_node(temp_state)
    
    for output in temp_state.agent_outputs:
        if output.get("agent") == "contact_agent":
            result = output.get("result", {})
            if result.get("status") == "contact_found":
                return {
                    "id": result.get("contact_id"),
                    "name": result.get("name"),
                    "email": result.get("email"),
                    "tone_preference": result.get("tone_preference"),
                    "relationship": result.get("relationship"),
                    "tags": result.get("tags", []),
                    "notes": result.get("notes", ""),
                }
    
    state.add_agent_output(
        agent="email_sender_agent",
        result={"status": "error", "reason": "contact_not_found"},
        score=0.0,
    )
    return None


def check_last_email_sent(contact_email: str) -> Dict:
    """Check when we last emailed this contact"""
    try:
        # Search Gmail for last email to this contact
        query = f"to:{contact_email} OR from:{contact_email}"
        emails = search_emails(query, max_results=5)
        
        if not emails:
            return {"date": None, "days_since": None, "count": 0}
        
        # Find most recent email
        latest_email = max(emails, key=lambda x: x.get("date", ""))
        
        # Calculate days since
        if "date" in latest_email:
            try:
                # Handle different date formats
                date_str = latest_email["date"]
                if 'T' in date_str:
                    email_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    # Try other formats
                    email_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                days_since = (datetime.now() - email_date).days
                return {
                    "date": latest_email["date"],
                    "days_since": days_since,
                    "count": len(emails),
                    "subject": latest_email.get("subject"),
                    "thread_id": latest_email.get("threadId"),
                }
            except:
                pass
        
        return {"date": None, "days_since": None, "count": len(emails)}
        
    except Exception as e:
        logger.error(f"Error checking last email: {e}")
        return {"date": None, "days_since": None, "count": 0, "error": str(e)}


def get_contact_memories(rag_service, contact: Dict) -> List[Dict]:
    """Get RAG memories about this contact"""
    try:
        # Query RAG for contact-specific memories
        queries = [
            f"conversation with {contact['name']}",
            f"email to {contact['name']}",
            f"meeting with {contact['name']}",
            f"preferences of {contact['name']}",
            contact.get("relationship", ""),
            contact.get("tone_preference", ""),
        ]
        
        all_memories = []
        seen_summaries = set()
        
        for query in queries:
            if not query.strip():
                continue
                
            memories = rag_service.query_memory(query=query, top_k=2)
            for mem in memories:
                summary = mem.get("summary", "")
                if summary and summary not in seen_summaries:
                    seen_summaries.add(summary)
                    all_memories.append(mem)
        
        return all_memories[:5]  # Limit to 5 most relevant
        
    except Exception as e:
        logger.warning(f"Error getting RAG contact memories: {e}")
        return []


def get_topic_memories(rag_service, email_ctx: Dict, contact: Dict) -> List[Dict]:
    """Get RAG memories about the email topic"""
    try:
        topic = email_ctx.get("subject", "").lower()
        body_keywords = extract_keywords(email_ctx.get("draft_reply", ""))
        
        queries = []
        if topic:
            queries.append(topic)
        if body_keywords:
            queries.extend(body_keywords[:3])
        
        # Add contact-specific topic queries
        if contact.get("name"):
            for query in list(queries)[:2]:  # Take first 2 queries
                queries.append(f"{query} {contact['name']}")
        
        all_memories = []
        seen_summaries = set()
        
        for query in queries:
            if not query.strip():
                continue
                
            memories = rag_service.query_memory(query=query, top_k=2)
            for mem in memories:
                summary = mem.get("summary", "")
                if summary and summary not in seen_summaries:
                    seen_summaries.add(summary)
                    all_memories.append(mem)
        
        return all_memories[:3]  # Limit to 3 most relevant
        
    except Exception as e:
        logger.warning(f"Error getting RAG topic memories: {e}")
        return []


def extract_keywords(text: str) -> List[str]:
    """Extract simple keywords from text"""
    if not text:
        return []
    
    # Remove common words and get unique words
    stop_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "with", "by", "is", "are", "was", "were", "be", "been", "being"}
    words = text.lower().split()
    keywords = [word.strip('.,!?;:"()[]{}') for word in words 
                if word.strip('.,!?;:"()[]{}') not in stop_words 
                and len(word.strip('.,!?;:"()[]{}')) > 3]
    return list(set(keywords))[:5]


def decide_if_should_send(
    contact: Dict, 
    last_email: Dict, 
    email_ctx: Dict,
    rag_context: Dict
) -> tuple:
    """Smart decision: Should we send this email? Using RAG memories"""
    
    # Rule 1: Check if we emailed too recently
    if last_email.get("days_since") is not None and last_email["days_since"] < 1:
        return False, "emailed_today"
    
    # Rule 2: Check RAG for contact preferences/red flags
    for memory in rag_context.get("contact_memories", []):
        summary = memory.get("summary", "").lower()
        
        # Check for do-not-email patterns
        if any(pattern in summary for pattern in [
            "do not email", 
            "unsubscribed", 
            "stop contact",
            "asked to stop",
            "no further contact"
        ]):
            return False, "rag_do_not_email"
        
        # Check for negative patterns
        if any(pattern in summary for pattern in [
            "angry response",
            "complained about",
            "negative reaction",
            "frustrated with",
            "annoyed by"
        ]):
            return False, "rag_negative_memory"
    
    # Rule 3: Check contact relationship and frequency
    relationship = contact.get("relationship", "").lower()
    email_count = last_email.get("count", 0)
    
    if relationship == "cold" and email_count >= 2:
        return False, "too_many_cold_emails"
    
    if relationship == "lead" and email_count >= 3 and last_email.get("days_since", 100) < 14:
        return False, "too_frequent_leads"
    
    # Rule 4: Check urgency
    if email_ctx.get("urgency") == "low" and last_email.get("days_since", 100) < 7:
        # But check RAG for exceptions
        has_important_context = False
        for memory in rag_context.get("topic_memories", []):
            summary = memory.get("summary", "").lower()
            if "important" in summary or "urgent" in summary or "critical" in summary:
                has_important_context = True
                break
        
        if not has_important_context:
            return False, "not_urgent_enough"
    
    # Rule 5: Check RAG for positive patterns (reasons TO send)
    for memory in rag_context.get("contact_memories", []):
        summary = memory.get("summary", "").lower()
        
        # Positive patterns that encourage emailing
        if any(pattern in summary for pattern in [
            "responds well to",
            "appreciated email",
            "positive interaction",
            "good relationship",
            "regular contact"
        ]):
            return True, "rag_positive_pattern"
    
    # Default: Send if none of the above blocks it
    return True, "approved_to_send"


def create_personalized_email(
    email_ctx: Dict, 
    contact: Dict, 
    rag_context: Dict,
    last_email: Dict
) -> Dict:
    """Create personalized email using RAG context"""
    
    base_body = email_ctx.get("draft_reply", "")
    base_subject = email_ctx.get("subject", "Follow up")
    
    # Apply tone
    tone = contact.get("tone_preference", "casual")
    body_with_tone = apply_rag_informed_tone(base_body, tone, contact, rag_context)
    
    # Add personal references from RAG
    personalized_body = add_rag_personalization(body_with_tone, rag_context, last_email)
    
    # Update subject if needed
    subject = personalize_subject(base_subject, rag_context, contact)
    
    return {
        "subject": subject,
        "body": personalized_body,
        "tone": tone,
        "personalized": True,
    }


def apply_rag_informed_tone(body: str, tone: str, contact: Dict, rag_context: Dict) -> str:
    """Apply tone based on contact preferences AND RAG memories"""
    
    # Check RAG for tone preferences
    preferred_tone = tone
    for memory in rag_context.get("contact_memories", []):
        summary = memory.get("summary", "")
        if "prefers formal tone" in summary.lower():
            preferred_tone = "formal"
        elif "likes casual communication" in summary.lower():
            preferred_tone = "casual"
        elif "appreciates friendly emails" in summary.lower():
            preferred_tone = "friendly"
    
    # Apply the tone
    tone_map = {
        "formal": {
            "greeting": "Dear",
            "closing": "Sincerely yours",
            "style": "professional",
            "phrases": ["I hope this message finds you well", "Thank you for your time"]
        },
        "casual": {
            "greeting": "Hi",
            "closing": "Best",
            "style": "relaxed",
            "phrases": ["Hope you're having a good week", "Thanks"]
        },
        "friendly": {
            "greeting": "Hello",
            "closing": "Warm regards",
            "style": "warm",
            "phrases": ["Great to connect", "Looking forward to hearing from you"]
        }
    }
    
    settings = tone_map.get(preferred_tone, tone_map["casual"])
    
    # Apply greeting and closing
    if contact.get("relationship") == "client":
        greeting = f"{settings['greeting']} {contact['name'].split()[0] if ' ' in contact['name'] else contact['name']},"
    else:
        greeting = f"{settings['greeting']},"
    
    formatted_body = f"{greeting}\n\n{body}\n\n{settings['closing']},\n\n[Your Name]"
    
    # Add tone-appropriate phrase if body is short
    if len(body) < 200 and settings['phrases']:
        phrase = random.choice(settings['phrases'])
        formatted_body = formatted_body.replace(greeting, f"{greeting}\n\n{phrase}")
    
    return formatted_body


def add_rag_personalization(body: str, rag_context: Dict, last_email: Dict) -> str:
    """Add personal touches from RAG memories"""
    
    personalizations = []
    
    # Check for recent conversations in RAG
    for memory in rag_context.get("contact_memories", []):
        summary = memory.get("summary", "").lower()
        
        if "recent conversation about" in summary.lower():
            topic_start = summary.lower().find("about")
            if topic_start != -1:
                topic = summary[topic_start+6:].split(".")[0]
                if topic.strip():
                    personalizations.append(f"Following up on our recent conversation about {topic}...")
        
        elif "mentioned interest in" in summary.lower():
            interest_start = summary.lower().find("in")
            if interest_start != -1:
                interest = summary[interest_start+3:].split(".")[0]
                if interest.strip():
                    personalizations.append(f"I remember you mentioned interest in {interest}...")
    
    # Add reference to last email if recent
    if last_email.get("days_since") and last_email["days_since"] < 30:
        personalizations.append("Following up on my previous email...")
    
    # Add personalizations to body
    if personalizations:
        # Add after greeting but before main content
        lines = body.split('\n')
        if len(lines) > 2:
            # Find where greeting ends (first blank line after greeting)
            greeting_end = 0
            for i, line in enumerate(lines):
                if i > 0 and line.strip() == "":
                    greeting_end = i
                    break
            
            if greeting_end == 0:
                greeting_end = 1
            
            # Insert personalizations
            personalized_lines = lines[:greeting_end] + [''] + personalizations + [''] + lines[greeting_end:]
            body = '\n'.join(personalized_lines)
    
    return body


def personalize_subject(subject: str, rag_context: Dict, contact: Dict) -> str:
    """Personalize subject line based on RAG"""
    
    # Check for ongoing topics
    for memory in rag_context.get("topic_memories", []):
        summary = memory.get("summary", "")
        if "ongoing discussion" in summary.lower() or "continued conversation" in summary.lower():
            # Add "Re: " if not already there
            if not subject.lower().startswith(("re:", "fw:", "fwd:")):
                subject = f"Re: {subject}"
            break
    
    # Add contact name for VIPs
    if contact.get("relationship") in ["vip", "key_client", "important"]:
        # Extract first name
        first_name = contact['name'].split()[0] if ' ' in contact['name'] else contact['name']
        subject = f"{first_name}: {subject}"
    
    return subject


def store_email_memory(rag_service, contact: Dict, email: Dict, draft: Dict, decision_reason: str):
    """Store this email interaction in RAG memory"""
    try:
        memory_content = f"""
        Sent email to {contact['name']} ({contact['email']})
        Relationship: {contact.get('relationship', 'unknown')}
        Tone used: {email['tone']}
        Subject: {email['subject']}
        Decision reason: {decision_reason}
        Draft created: {datetime.now().isoformat()}
        Contains personalization based on previous interactions
        """
        
        memory_id = rag_service.store_memory(
            content=memory_content,
            memory_type="email_interaction",
            metadata={
                "contact_id": contact["id"],
                "contact_name": contact["name"],
                "tone": email["tone"],
                "draft_id": draft.get("id"),
                "relationship": contact.get("relationship"),
                "decision_reason": decision_reason,
            }
        )
        
        if memory_id:
            logger.info(f"Stored email memory: {memory_id}")
        else:
            logger.warning("Failed to store email memory")
            
    except Exception as e:
        logger.error(f"Failed to store email memory in RAG: {e}")