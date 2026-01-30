
from __future__ import annotations
import logging
from typing import Dict, Any

from app.graph.state import PresentOSState
from app.integrations.gmail_client import fetch_unread_messages, create_draft
from app.services.email_triage import triage_email
from app.utils.instruction_utils import get_instruction

logger = logging.getLogger("presentos.email_agent")


def run_email_node(state: PresentOSState) -> PresentOSState:
    """
    Email Agent (Proactive V2)
    
    Capabilities:
    1. Scan Inbox (FETCH -> TRIAGE -> SIGNAL)
    2. Draft Replies (EXECUTE)
    3. Extract Tasks (SIGNAL)
    """

    instruction = get_instruction(state, "email_agent")
    if not instruction:
        return state

    intent = instruction.get("intent")
    payload = instruction.get("payload", {})

    # -------------------------------------------------------
    # 1. CHECK EMAILS (User-facing command)
    # -------------------------------------------------------
    if intent in ["check_emails", "check_email", "read_emails"]:
        # Alias to scan_inbox
        intent = "scan_inbox"
        if "max_results" not in payload:
            payload["max_results"] = 5

    # -------------------------------------------------------
    # 2. SCAN INBOX (Proactive Loop)
    # -------------------------------------------------------
    if intent == "scan_inbox":
        max_results = payload.get("max_results", 5)
        logger.info(f"Scanning inbox (max={max_results})...")
        
        try:
            emails = fetch_unread_messages(max_results=max_results)
            
            scan_results = []
            new_tasks = []
            
            for email in emails:
                # Triage each email
                triage = triage_email(email)
                
                email_summary = {
                    "id": email.get("id"),
                    "subject": email.get("subject"),
                    "from": email.get("from"),
                    "triage": triage
                }
                scan_results.append(email_summary)
                
                # Signal: Task Extraction
                if triage.get("needs_task"):
                    task_signal = {
                        "agent": "task_agent",
                        "intent": "create_task",
                        "payload": {
                            "title": f"Follow up: {triage.get('summary')}",
                            "description": f"Source: Email from {email.get('from')}\\n\\nContext: {email.get('snippet')}",
                            "priority": triage.get("priority", "medium"),
                            "paei_hint": triage.get("paei", "A")
                        }
                    }
                    new_tasks.append(task_signal)
                    state.add_agent_output("email_agent", {"signal": "task_detected", "task": task_signal})
            
            state.add_agent_output(
                agent="email_agent",
                result={
                    "action": "inbox_scanned",
                    "emails_found": len(emails),
                    "actionable_count": len(new_tasks),
                    "scanned_items": scan_results
                },
                score=1.0
            )
            return state
            
        except Exception as e:
            logger.exception("Inbox scan failed")
            state.add_agent_output("email_agent", {"error": str(e)})
            return state

    # -------------------------------------------------------
    # 2. READ / TRIAGE SINGLE EMAIL (Legacy/Direct)
    # -------------------------------------------------------
    email = payload.get("email")
    if email:
        try:
            triage = triage_email(email)
            state.add_agent_output("email_agent", {"triage": triage}, score=0.9)
            return state
        except Exception as e:
            logger.exception("Email triage failed")
            return state

    # -------------------------------------------------------
    # 3. DRAFT REPLY (with RAG Tone)
    # -------------------------------------------------------
    if intent == "draft_reply":
        logger.info("Drafting reply...")
        
        # Extract context
        to = payload.get("to")
        subject = payload.get("subject", "No Subject")
        context_notes = payload.get("context_notes", "")
        tone_context = payload.get("tone_context", "")  # From RAG
        thread_id = payload.get("thread_id")
        
        # Generate Draft via LLM (Internal Thought)
        from app.services.email_triage import client as llm_client
        
        draft_prompt = f"""
        You are the user. Write a email reply.
        
        USER TONE/STYLE (Emulate this):
        {tone_context or "Professional but warm, concise."}
        
        CONTEXT/INSTRUCTIONS:
        {context_notes}
        
        Recipient: {to}
        Subject: {subject}
        
        Draft the body only. No subject line.
        """
        
        try:
            resp = llm_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": draft_prompt}],
                temperature=0.7
            )
            draft_body = resp.choices[0].message.content.strip()
            
            # Create Gmail Draft
            draft = create_draft(
                to=to,
                subject=subject,
                body=draft_body,
                thread_id=thread_id
            )
            
            state.add_agent_output(
                agent="email_agent",
                result={
                    "action": "draft_created",
                    "draft_id": draft.get("id"),
                    "preview": draft_body[:100] + "..."
                },
                score=1.0
            )
            return state
            
        except Exception as e:
            logger.exception("Draft creation failed")
            state.add_agent_output("email_agent", {"error": str(e)})
            return state

    # -------------------------------------------------------
    # 4. SEND EMAIL (New - Actual Sending)
    # -------------------------------------------------------
    if intent == "send_email":
        logger.info("📧 Sending email...")
        
        # Extract payload
        recipient = payload.get("recipient") or payload.get("to")
        subject = payload.get("subject", "Message from PresentOS")
        body = payload.get("body") or payload.get("message")
        
        # If no recipient, fail gracefully
        if not recipient:
            logger.error("No recipient specified for email")
            state.add_agent_output(
                agent="email_agent",
                result={
                    "action": "email_send_failed",
                    "error": "No recipient specified"
                },
                score=0.0
            )
            return state
        
        # If no body provided, generate one
        if not body:
            from app.services.email_triage import client as llm_client
            
            prompt = f"""
            Generate a brief, professional email to {recipient}.
            Subject: {subject}
            
            Write a short, friendly message (2-3 sentences).
            Be warm but professional.
            """
            
            try:
                resp = llm_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                body = resp.choices[0].message.content.strip()
            except Exception as e:
                logger.error(f"Failed to generate email body: {e}")
                body = f"Hello,\n\nThis is a message from PresentOS.\n\nBest regards"
        
        try:
            from app.integrations.gmail_client import send_email
            
            sent_message = send_email(
                to=recipient,
                subject=subject,
                body=body
            )
            
            logger.info(f"✅ Email sent to {recipient}")
            
            state.add_agent_output(
                agent="email_agent",
                result={
                    "action": "email_sent",
                    "message_id": sent_message.get("id"),
                    "recipient": recipient,
                    "subject": subject,
                    "body_preview": body[:100] + "..." if len(body) > 100 else body
                },
                score=1.0
            )
            return state
            
        except Exception as e:
            logger.exception("Email send failed")
            state.add_agent_output(
                agent="email_agent",
                result={
                    "action": "email_send_failed",
                    "error": str(e),
                    "recipient": recipient
                },
                score=0.0
            )
            return state

    return state
