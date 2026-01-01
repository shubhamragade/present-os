# app/integrations/pinecone_client.py

"""
Pinecone Client for PresentOS (LOW-LEVEL VECTOR STORE).

PDF RULES:
- Stores ONLY compressed summaries (no raw logs)
- ParentAgent READS via RAGService only
- Child agents NEVER touch Pinecone
- RAGService is the ONLY writer
- This client is a THIN DB ADAPTER (NO LOGIC)

INDEX:
- name: presentos-memory-1536
- dim: 1536
- metric: cosine
"""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from pinecone import Pinecone
from app.config.settings import settings

logger = logging.getLogger("presentos.pinecone")


VECTOR_DIMENSION = 1536


class PineconeClient:
    """
    Thin wrapper around Pinecone index.

    RESPONSIBILITIES:
    - upsert vectors
    - query vectors
    - ZERO intelligence
    - ZERO embeddings
    - ZERO summarization
    """

    def __init__(
        self,
        api_key: str,
        index_name: str,
        host: Optional[str] = None,
        default_namespace: str = "user_patterns",
    ):
        self.index_name = index_name
        self.default_namespace = default_namespace

        self.pc = Pinecone(api_key=api_key)

        if host:
            self.index = self.pc.Index(index_name, host=host)
        else:
            self.index = self.pc.Index(index_name)

        logger.info(
            "PineconeClient initialized index=%s namespace=%s",
            index_name,
            default_namespace,
        )

    # ---------------------------------------------------------
    # FACTORY
    # ---------------------------------------------------------
    @classmethod
    def from_env(cls) -> "PineconeClient":
        if not settings.PINECONE_API_KEY:
            raise RuntimeError("PINECONE_API_KEY not set")

        if not settings.PINECONE_INDEX:
            raise RuntimeError("PINECONE_INDEX not set")

        return cls(
            api_key=settings.PINECONE_API_KEY,
            index_name=settings.PINECONE_INDEX,
            host=settings.PINECONE_HOST,
            default_namespace=settings.RAG_NAMESPACE or "user_patterns",
        )

    # ---------------------------------------------------------
    # WRITE (RAGService ONLY)
    # ---------------------------------------------------------
    def upsert(
        self,
        vectors: List[Dict[str, Any]],
        namespace: Optional[str] = None,
    ) -> None:
        """
        Upsert vectors.

        Expected format:
        {
          "id": str,
          "values": List[float] (len=1536),
          "metadata": dict
        }
        """

        if not vectors:
            logger.warning("Pinecone upsert called with empty vectors")
            return

        ns = namespace or self.default_namespace

        # Validate vectors defensively
        safe_vectors = []
        for v in vectors:
            values = v.get("values")
            if not values or len(values) != VECTOR_DIMENSION:
                logger.warning("Skipping invalid vector id=%s", v.get("id"))
                continue

            safe_vectors.append(
                {
                    "id": v["id"],
                    "values": values,
                    "metadata": v.get("metadata", {}),
                }
            )

        if not safe_vectors:
            logger.warning("No valid vectors to upsert after validation")
            return

        try:
            self.index.upsert(
                vectors=safe_vectors,
                namespace=ns,
            )
            logger.info("Upserted %d vectors into namespace=%s", len(safe_vectors), ns)

        except Exception as e:
            logger.exception("Pinecone upsert failed")
            raise

    # ---------------------------------------------------------
    # READ (RAGService / ParentAgent)
    # ---------------------------------------------------------
    def query(
        self,
        vector: List[float],
        top_k: int = 3,
        namespace: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query Pinecone.

        RETURNS:
        Raw matches ONLY.
        Caller decides interpretation.
        """

        if not vector or len(vector) != VECTOR_DIMENSION:
            logger.warning("Invalid query vector")
            return []

        ns = namespace or self.default_namespace

        try:
            response = self.index.query(
                vector=vector,
                top_k=top_k,
                namespace=ns,
                include_metadata=True,
                filter=filter,
            )

            # Pinecone SDK v3+
            matches = response.matches or []

            logger.info("Pinecone returned %d matches", len(matches))
            return matches

        except Exception as e:
            logger.exception("Pinecone query failed")
            return []
