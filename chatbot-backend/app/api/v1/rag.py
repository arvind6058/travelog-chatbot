from typing import Any, Dict, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.ai.orchestrator import orchestrator

router = APIRouter(prefix="/rag", tags=["RAG & Knowledge Base"])


class RagQueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=2000, description="Knowledge base search query")
    category: Optional[str] = Field(None, description="Optional category filter (e.g., policy, travel, logistics)")


@router.post("/search", summary="Search backend policy and knowledge base")
async def rag_search_endpoint(
    payload: RagQueryRequest,
    db: AsyncSession = Depends(get_db_session),
):
    """
    Backend RAG search endpoint for Travelogix policies, FAQs, and service guidelines.
    """
    result = await orchestrator.process_message(
        db=db,
        message=f"Policy RAG: {payload.query}",
    )
    return {
        "success": True,
        "query": payload.query,
        "results": [
            {
                "topic": "travelogix_policies",
                "content": result.get("reply"),
                "provenance": result.get("provenance") or {
                    "source": "travelogix_knowledge_base",
                    "mode": "rag",
                    "is_mock": False,
                    "fetched_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        ],
    }


@router.post("/query", summary="Query backend RAG for synthesized policy answers")
async def rag_query_endpoint(
    payload: RagQueryRequest,
    db: AsyncSession = Depends(get_db_session),
):
    result = await orchestrator.process_message(
        db=db,
        message=f"Policy RAG: {payload.query}",
    )
    return {
        "success": True,
        "query": payload.query,
        "answer": result.get("reply"),
        "provenance": result.get("provenance") or {
            "source": "travelogix_knowledge_base",
            "mode": "rag",
            "is_mock": False,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        },
    }
