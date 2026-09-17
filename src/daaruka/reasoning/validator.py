"""Grounding validation engine ensuring all emitted recommendations strictly map to verified chunks."""

import logging
from typing import List, Dict, Tuple
from daaruka.knowledge.models import RetrievedChunk
from daaruka.reasoning.models import Recommendation, RecommendationSource

logger = logging.getLogger(__name__)


class GroundingValidationError(Exception):
    """Raised when an ungrounded or hallucinated recommendation fails strict validation."""
    pass


def validate_and_filter_recommendations(
    recommendations: List[Recommendation],
    available_chunks_map: Dict[str, RetrievedChunk],
    strict: bool = False,
) -> Tuple[List[Recommendation], List[str]]:
    """Validate that every recommendation is strictly grounded in retrieved vector database chunks.

    Enforces:
    1. Every `source` item in `recommendation.sources` must reference a `chunk_id` present in `available_chunks_map`.
    2. The citation metadata (publisher, year, page) must match the real chunk's citation.
    3. `variable_interactions` must contain at least 2 interacting variables.

    Returns:
        Tuple of (valid_recommendations, validation_errors_log).
    """
    valid_recommendations: List[Recommendation] = []
    error_log: List[str] = []

    for rec_idx, rec in enumerate(recommendations):
        rec_errors = []

        # 1. Check multi-variable interaction constraint
        if len(rec.variable_interactions) < 2:
            rec_errors.append(
                f"Recommendation '{rec.action}' only specifies {len(rec.variable_interactions)} variable interaction(s). Minimum 2 required."
            )

        # 2. Check source grounding
        if not rec.sources:
            rec_errors.append(f"Recommendation '{rec.action}' has no source citations attached.")

        valid_sources: List[RecommendationSource] = []
        for src in rec.sources:
            if src.chunk_id not in available_chunks_map:
                rec_errors.append(
                    f"Ungrounded chunk_id '{src.chunk_id}' cited in '{rec.action}'. Chunk does not exist in retrieved set."
                )
            else:
                real_chunk = available_chunks_map[src.chunk_id]
                # Ensure citation matches real chunk
                c = real_chunk.citation
                validated_src = RecommendationSource(
                    chunk_id=src.chunk_id,
                    document_title=c.document_title,
                    publisher=c.publisher,
                    year=c.year,
                    section_title=c.section_title,
                    page=c.page,
                    url_or_doi=c.url_or_doi,
                    citation=c.citation_string(),
                )
                valid_sources.append(validated_src)

        if rec_errors:
            msg = f"Validation failure on recommendation #{rec_idx + 1} ('{rec.action}'): {'; '.join(rec_errors)}"
            logger.warning(msg)
            error_log.append(msg)
            if strict:
                raise GroundingValidationError(msg)
        else:
            # Reconstruct with verified real sources
            rec.sources = valid_sources
            valid_recommendations.append(rec)

    return valid_recommendations, error_log
