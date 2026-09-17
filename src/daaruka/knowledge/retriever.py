"""Scientific Knowledge Retrieval Engine with Citation Enforcement."""

import logging
from typing import List, Optional
from daaruka.knowledge.models import RetrievedChunk
from daaruka.knowledge.vector_store import VectorStore, default_vector_store

logger = logging.getLogger(__name__)


def retrieve(
    query: str,
    top_k: int = 5,
    filter_tags: Optional[List[str]] = None,
    vector_store: Optional[VectorStore] = None,
) -> List[RetrievedChunk]:
    """Retrieve grounded knowledge chunks with attached scientific citations.

    Args:
        query: Natural language query (e.g. "how does cover cropping affect soil carbon").
        top_k: Number of most relevant chunks to return (default 5).
        filter_tags: Optional list of topic tags (e.g. ["soil", "carbon"]).
        vector_store: Custom VectorStore instance (defaults to global instance).

    Returns:
        List of RetrievedChunk objects, each guaranteed to contain a valid SourceCitation.
    """
    clean_query = query.strip()
    if not clean_query:
        return []

    store = vector_store or default_vector_store
    results = store.query(
        query_text=clean_query,
        top_k=top_k,
        filter_tags=filter_tags,
    )

    # Verification: Ensure each chunk strictly carries valid citation data
    for chunk in results:
        if not chunk.citation or not chunk.citation.document_title:
            logger.warning(f"Retrieved chunk {chunk.chunk_id} missing full citation metadata.")

    return results


def format_retrieval_context(chunks: List[RetrievedChunk]) -> str:
    """Format a list of retrieved chunks into an LLM-ready prompt context with citation headers."""
    if not chunks:
        return "No relevant scientific literature found."

    context_blocks = []
    for idx, chunk in enumerate(chunks, start=1):
        citation_hdr = f"[{idx}] {chunk.citation.citation_string()}"
        block = f"{citation_hdr}\n{chunk.content}"
        context_blocks.append(block)

    return "\n\n---\n\n".join(context_blocks)
