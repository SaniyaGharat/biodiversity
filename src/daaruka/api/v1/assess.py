"""Structured Site Assessment API v1 endpoint for machine-to-machine reasoning."""

from fastapi import APIRouter, HTTPException, status
from daaruka.reasoning.models import SiteAssessmentInput, ReasoningAssessmentOutput
from daaruka.reasoning.engine import default_reasoning_engine

router = APIRouter(tags=["Assessment"])


@router.post(
    "",
    response_model=ReasoningAssessmentOutput,
    status_code=status.HTTP_200_OK,
    summary="Direct multi-metric site assessment endpoint",
    description=(
        "Processes structured SiteAssessmentInput JSON directly without conversational extraction, "
        "auto-enriches missing soil and biodiversity metrics if lat/long are provided, and returns "
        "synthesized, scientifically grounded recommendations with full provenance and page citations."
    ),
)
async def perform_site_assessment(assessment: SiteAssessmentInput) -> ReasoningAssessmentOutput:
    """Execute direct multi-metric assessment over structured input."""
    try:
        output = await default_reasoning_engine.evaluate_async(assessment)
        return output
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating site assessment: {str(e)}",
        )
