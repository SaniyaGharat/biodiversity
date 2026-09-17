"""Reasoning Module for Daaruka Biodiversity Intelligence Platform.

Exposes:
- `SiteAssessmentInput`: Pydantic input schema for site conditions.
- `ReasoningAssessmentOutput`: Comprehensive multi-metric reasoning payload.
- `Recommendation`: Scientifically grounded, multi-variable recommendation schema.
- `detect_gaps`: Identifies missing ecological categories and suggests clarification prompts.
- `evaluate_site`: Executes complete multi-metric reasoning pipeline.
- `MultiMetricReasoningEngine`: Core orchestrator class.
- `validate_and_filter_recommendations`: Strict grounding validator.
"""

from daaruka.reasoning.models import (
    SiteAssessmentInput,
    GapAnalysisResult,
    Recommendation,
    RecommendationSource,
    ReasoningAssessmentOutput,
)
from daaruka.reasoning.gap_detector import detect_gaps
from daaruka.reasoning.validator import (
    validate_and_filter_recommendations,
    GroundingValidationError,
)
from daaruka.reasoning.engine import (
    MultiMetricReasoningEngine,
    default_reasoning_engine,
    evaluate_site,
)

__all__ = [
    "SiteAssessmentInput",
    "GapAnalysisResult",
    "Recommendation",
    "RecommendationSource",
    "ReasoningAssessmentOutput",
    "detect_gaps",
    "validate_and_filter_recommendations",
    "GroundingValidationError",
    "MultiMetricReasoningEngine",
    "default_reasoning_engine",
    "evaluate_site",
]
