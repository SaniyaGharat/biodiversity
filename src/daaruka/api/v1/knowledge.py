"""API endpoints for scientific knowledge retrieval."""

from typing import Optional, List
from fastapi import APIRouter, Query
from daaruka.knowledge.models import KnowledgeSearchResponse
from daaruka.knowledge.retriever import retrieve

router = APIRouter(tags=["Knowledge"])


@router.get(
    "/search",
    response_model=KnowledgeSearchResponse,
    summary="Semantic Knowledge Retrieval",
    description=(
        "Performs semantic search over peer-reviewed scientific reports (FAO, IPCC, IPBES, CBD) "
        "and returns text chunks strictly paired with standardized source citations."
    ),
)
async def search_knowledge(
    query: str = Query(..., description="Natural language search query", min_length=2),
    top_k: int = Query(default=5, ge=1, le=20, description="Number of relevant chunks to retrieve"),
    tags: Optional[str] = Query(
        default=None,
        description="Comma-separated topic tags to filter (e.g. 'soil,carbon' or 'biodiversity')",
    ),
) -> KnowledgeSearchResponse:
    """Execute knowledge retrieval query with citation metadata."""
    filter_tags: Optional[List[str]] = None
    if tags:
        filter_tags = [t.strip().lower() for t in tags.split(",") if t.strip()]

    chunks = retrieve(query=query, top_k=top_k, filter_tags=filter_tags)

    return KnowledgeSearchResponse(
        query=query,
        total_results=len(chunks),
        results=chunks,
    )
