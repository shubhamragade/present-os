# app/services/rag_service.py
"""
RAG (Retrieval-Augmented Generation) Memory Service for Present OS.

RESPONSIBILITIES:
- Compress events/tasks/XP into short semantic memories
- Generate 1536-dim embeddings
- Store + retrieve long-term memory from Pinecone
- NEVER store raw conversation logs
- NEVER make decisions (utility only)

USED BY:
- ParentAgent (read)
- Background workers (write)
"""

from __future__ import annotations

import logging
import re
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional

from openai import OpenAI

from app.config.settings import settings
from app.integrations.pinecone_client import PineconeClient

logger = logging.getLogger("presentos.rag")

EMBEDDING_DIM = 1536


# ---------------------------------------------------------
# RAG Service
# ---------------------------------------------------------
class RAGService:
    """
    Long-term memory manager for Present OS.
    """

    def __init__(
        self,
        pinecone: PineconeClient,
        model: str = "gpt-4o-mini",
        embedding_model: str = "text-embedding-3-small",
        namespace: str = "user_patterns",
    ):
        self.pinecone = pinecone
        self.namespace = namespace
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model
        self.embedding_model = embedding_model

    # -----------------------------------------------------
    # PUBLIC: WRITE MEMORY (background workers only)
    # -----------------------------------------------------
    def store_memory(
        self,
        content: str,
        memory_type: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Store a compressed memory safely.
        Returns memory_id or None on failure.
        """

        if not content or not memory_type:
            return None

        metadata = metadata or {}

        try:
            # 1. Sanitize content (hard guardrail)
            safe_content = self._sanitize(content)

            # 2. Summarize
            summary = self._summarize(safe_content, memory_type)
            if not summary:
                return None

            # 3. Embed
            embedding = self._embed(summary)
            if not embedding or len(embedding) != EMBEDDING_DIM:
                logger.warning("Invalid embedding size")
                return None

            # 4. Build record
            memory_id = f"mem-{uuid.uuid4().hex}"
            record = {
                "id": memory_id,
                "values": embedding,
                "metadata": {
                    "summary": summary,
                    "type": memory_type,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    **metadata,
                },
            }

            # 5. Store
            self.pinecone.upsert(
                vectors=[record],
                namespace=self.namespace,
            )

            logger.info("Stored memory %s (%s)", memory_id, memory_type)
            return memory_id

        except Exception:
            logger.exception("RAG store_memory failed")
            return None

    # -----------------------------------------------------
    # PUBLIC: READ MEMORY (ParentAgent only)
    # -----------------------------------------------------
    def query_memory(
        self,
        query: str,
        top_k: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant long-term memory summaries.
        Deduplicated by summary.
        """

        if not query:
            return []

        try:
            embedding = self._embed(query)
            if not embedding:
                return []

            results = self.pinecone.query(
                vector=embedding,
                top_k=top_k,
                namespace=self.namespace,
            )

            memories: List[Dict[str, Any]] = []
            seen_summaries = set()

            for match in results or []:
                meta = match.get("metadata", {})
                summary = meta.get("summary")

                if not summary or summary in seen_summaries:
                    continue

                seen_summaries.add(summary)

                memories.append(
                    {
                        "summary": summary,
                        "type": meta.get("type"),
                        "timestamp": meta.get("timestamp"),
                        "score": round(float(match.get("score", 0.0)), 3),
                    }
                )

            return memories

        except Exception:
            logger.exception("RAG query_memory failed")
            return []

    # -----------------------------------------------------
    # INTERNAL: SANITIZATION
    # -----------------------------------------------------
    def _sanitize(self, text: str) -> str:
        """
        Remove obvious PII before LLM sees content.
        """
        text = re.sub(r"\S+@\S+", "[email]", text)
        text = re.sub(r"\b\d{3,}\b", "[number]", text)
        text = re.sub(r"\n+", " ", text)
        return text.strip()[:2000]

    # -----------------------------------------------------
    # INTERNAL: SUMMARIZATION
    # -----------------------------------------------------
    def _summarize(self, content: str, memory_type: str) -> Optional[str]:
        """
        Compress content into 1–2 factual sentences.
        """

        prompt = f"""
You are a long-term memory compression engine.

Memory type: {memory_type}

Rules:
- Extract patterns, outcomes, or preferences
- Remove names, emails, exact dates, and raw dialog
- Max TWO sentences
- Neutral factual tone
- NO bullet points

Content:
{content}
"""

        try:
            resp = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Compress experience into durable memory."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
            )

            summary = resp.choices[0].message.content.strip()
            return summary[:400]

        except Exception:
            logger.exception("RAG summarization failed")
            return None

    # -----------------------------------------------------
    # INTERNAL: EMBEDDING
    # -----------------------------------------------------
    def _embed(self, text: str) -> Optional[List[float]]:
        """
        Generate 1536-dim embedding.
        """

        try:
            resp = self.client.embeddings.create(
                model=self.embedding_model,
                input=text,
            )
            return resp.data[0].embedding
        except Exception:
            logger.exception("Embedding generation failed")
            return None


# ---------------------------------------------------------
# FACTORY
# ---------------------------------------------------------
def get_rag_service() -> RAGService:
    """
    Dependency-safe RAG service factory.
    """
    pinecone = PineconeClient.from_env()
    return RAGService(pinecone=pinecone)
