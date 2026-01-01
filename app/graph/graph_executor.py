# app/graph/graph_executor.py
"""
PresentOS Main Execution Graph - PDF-Compliant with Full Error Handling
"""

from __future__ import annotations
import logging
from typing import Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.graph.state import PresentOSState
from app.services.context_loader import load_context
from app.services.conversation_manager import ConversationManager
from app.services.intent_classifier import get_default_intent_classifier
from app.workers.memory_writer import process_memory

from app.integrations.notion_client import NotionClient
from app.graph.execution_router import ExecutionRouter
from app.graph.parent_node import run_parent_node
from app.graph.parent_response_node import run_parent_response_node

logger = logging.getLogger("presentos.graph")


class PresentOSGraph:
    """
    Complete PresentOS execution graph - PDF COMPLIANT
    
    Flow (PDF Pages 3-4):
    1. Conversation/Slot filling
    2. Context loading (RPM Goals)
    3. Intent classification  
    4. Parent decision (PAEI + Energy + RPM)
    5. Execution (PAEI-aware)
    6. Response generation
    7. Memory writing
    """
    
    def __init__(self):
        self.conversation = ConversationManager()
        self.intent_classifier = get_default_intent_classifier()
        self.notion = NotionClient.from_env()
        self.execution_router = ExecutionRouter(self.notion)
        
    def invoke(self, state: PresentOSState) -> PresentOSState:
        """Execute complete PresentOS flow - PDF Page 3 ONE chat interface"""
        
        logger.info(f"Graph invoked: '{state.input_text[:50]}...'")
        
        try:
            # 1️⃣ Conversation Management (PDF: natural language, not forms)
            state = self.conversation.process_user_message(state, state.input_text)
            if ConversationManager.is_slot_filling(state):
                logger.info("Slot filling in progress")
                return state
            
            # 2️⃣ Load Context (RPM Goals - PDF Page 5-6)
            state = load_context(state, self.notion)
            
            # 3️⃣ Intent Classification (PDF: natural language understanding)
            if state.intent is None:
                try:
                    state.intent = self.intent_classifier.classify(state.input_text)
                    logger.info(f"Intent classified: {len(state.intent.intents) if state.intent else 0} intents")
                except Exception as e:
                    logger.error(f"Intent classification failed: {e}")
                    # Create minimal intent to continue
                    from app.services.intent_classifier import IntentResult, SubIntent
                    state.intent = IntentResult(
                        intents=[SubIntent(intent="create_task", category="task", payload={"title": state.input_text})],
                        read_domains=[],
                        confidence=0.7,
                        explanation="Fallback intent",
                        model="fallback",
                        raw={}
                    )
            
            # 4️⃣ Parent Decision (PAEI + Energy + RPM - PDF Pages 4-5, 40-41)
            state = run_parent_node(state)
            
            # Check if we should proceed
            decision_context = (state.parent_decision or {}).get("decision_context", {})
            if not decision_context.get("should_proceed", True):
                logger.info("Parent decision: do not proceed")
                return state
            
            # 5️⃣ Execute Instructions (PAEI-aware - PDF: coordinated actions)
            instructions = (state.parent_decision or {}).get("instructions", [])
            if instructions:
                logger.info(f"Executing {len(instructions)} instructions")
                try:
                    state = self.execution_router(state)
                except Exception as e:
                    logger.error(f"Execution failed: {e}")
                    state.final_response = f"Execution failed: {str(e)[:100]}"
                    return state
            
            # 6️⃣ Update Conversation with Results
            state = self.conversation.handle_agent_outputs(state)
            
            # 7️⃣ Generate User-Facing Response (PDF: ONE unified response)
            state = run_parent_response_node(state)
            
            # 8️⃣ Write Memory (PDF Page 14: context accumulation)
            try:
                process_memory(state)
            except Exception as e:
                logger.error(f"Memory write failed: {e}")
                # Don't fail the whole flow for memory errors
            
            logger.info("Graph execution completed - PDF flow executed")
            return state
            
        except Exception as e:
            logger.error(f"Graph execution failed: {e}")
            state.final_response = "I encountered an error processing your request. Please try again."
            return state
    
    def process_streaming(
        self, 
        state: PresentOSState, 
        callback: Optional[callable] = None
    ) -> PresentOSState:
        """Process with streaming callbacks"""
        
        state = self.invoke(state)
        
        if callback and state.final_response:
            callback({
                "response": state.final_response,
                "paei_context": state.parent_decision.get("paei_decision", {}) if state.parent_decision else {},
                "xp_awarded": next(
                    (i["payload"].get("amount", 0) 
                     for i in (state.parent_decision or {}).get("instructions", [])
                     if i.get("agent") == "xp_agent"),
                    0
                )
            })
        
        return state


def build_presentos_graph() -> PresentOSGraph:
    """Factory function for dependency injection"""
    return PresentOSGraph()