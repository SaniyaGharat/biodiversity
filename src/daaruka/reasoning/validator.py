"""Grounding validation engine enforcing strict chunk provenance and numeric claim verification."""

import re
import logging
from typing import List, Dict, Tuple, Set
from daaruka.knowledge.models import RetrievedChunk
from daaruka.reasoning.models import Recommendation, RecommendationSource

logger = logging.getLogger(__name__)


class GroundingValidationError(Exception):
    """Raised when an ungrounded, hallucinated, or numerically unverified recommendation fails validation."""
    pass


def extract_numbers_from_text(text: str) -> Set[str]:
    """Extract distinct numbers, percentages, and metrics from text for grounding verification."""
    # Matches numbers with optional decimals and percent signs (e.g., '15%', '0.55', '30', '40%')
    raw_matches = re.findall(r"\b\d+(?:\.\d+)?%?\b", text)
    filtered = set()
    for m in raw_matches:
        val_clean = m.rstrip("%")
        try:
            val_float = float(val_clean)
            # Skip publication years (1900-2030)
            if 1900 <= val_float <= 2030:
                continue
            filtered.add(m)
            if "%" in m:
                filtered.add(val_clean)
        except ValueError:
            continue
    return filtered


def verify_numeric_grounding(estimated_effect: str, cited_chunks: List[RetrievedChunk]) -> Tuple[bool, List[str]]:
    """Check whether specific quantitative claims in estimated_effect are supported by the raw text or metadata of cited chunks.

    Returns:
        Tuple of (is_valid, list_of_unsupported_numbers)
    """
    effect_numbers = extract_numbers_from_text(estimated_effect)
    if not effect_numbers:
        return True, []

    # Combined text from chunks and metadata (pages, section titles)
    combined_source_text = " ".join(
        f"{c.content} Page {c.citation.page} {c.citation.section_title}" for c in cited_chunks
    )

    unsupported: List[str] = []
    for num in effect_numbers:
        num_clean = num.rstrip("%")
        pattern = rf"\b{re.escape(num_clean)}\b"
        if not re.search(pattern, combined_source_text):
            unsupported.append(num)

    if unsupported:
        return False, unsupported
    return True, []


def validate_and_filter_recommendations(
    recommendations: List[Recommendation],
    available_chunks_map: Dict[str, RetrievedChunk],
    strict: bool = False,
    enforce_numeric_grounding: bool = True,
) -> Tuple[List[Recommendation], List[str]]:
    """Validate that every recommendation is strictly grounded in retrieved vector database chunks.

    Enforces:
    1. Every `source` in `recommendation.sources` must reference a `chunk_id` present in `available_chunks_map`.
    2. The citation metadata (publisher, year, page) must match the real chunk's citation.
    3. `variable_interactions` must contain at least 2 interacting variables.
    4. Quantitative claims in `estimated_effect` must be supported by the cited chunks.

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
        matching_retrieved_chunks: List[RetrievedChunk] = []

        for src in rec.sources:
            if src.chunk_id not in available_chunks_map:
                rec_errors.append(
                    f"Ungrounded chunk_id '{src.chunk_id}' cited in '{rec.action}'. Chunk does not exist in retrieved set."
                )
            else:
                real_chunk = available_chunks_map[src.chunk_id]
                matching_retrieved_chunks.append(real_chunk)
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

        # 3. Check numeric grounding against cited chunk content
        if enforce_numeric_grounding and matching_retrieved_chunks:
            is_numeric_valid, unsupported_nums = verify_numeric_grounding(
                estimated_effect=rec.estimated_effect,
                cited_chunks=matching_retrieved_chunks,
            )
            if not is_numeric_valid:
                rec_errors.append(
                    f"Numeric hallucination detected in '{rec.action}': numbers {unsupported_nums} in estimated_effect do not appear in cited chunk text."
                )

        if rec_errors:
            msg = f"Validation failure on recommendation #{rec_idx + 1} ('{rec.action}'): {'; '.join(rec_errors)}"
            logger.warning(msg)
            error_log.append(msg)
            if strict:
                raise GroundingValidationError(msg)
        else:
            rec.sources = valid_sources
            valid_recommendations.append(rec)

    return valid_recommendations, error_log
