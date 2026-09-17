from typing import Optional, Union
from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import PlainTextResponse

from daaruka.reasoning.models import SiteAssessmentInput, ReasoningAssessmentOutput
from daaruka.reasoning.engine import default_reasoning_engine
from daaruka.chat.formatter import format_conversational_recommendations

router = APIRouter(tags=["Assessment"])


@router.post(
    "",
    response_model=Optional[ReasoningAssessmentOutput],
    status_code=status.HTTP_200_OK,
    summary="Direct multi-metric site assessment endpoint",
    description=(
        "Processes structured SiteAssessmentInput JSON directly without conversational extraction, "
        "auto-enriches missing soil and biodiversity metrics if lat/long are provided, and returns "
        "synthesized, scientifically grounded recommendations with full provenance and page citations. "
        "Supports ?format=text or ?format=markdown for rendered conversational output."
    ),
)
async def perform_site_assessment(
    assessment: SiteAssessmentInput,
    format: Optional[str] = Query(
        default="json",
        description="Response format: 'json' (default structured object) or 'text' / 'markdown' (rendered markdown).",
    ),
) -> Union[ReasoningAssessmentOutput, PlainTextResponse]:
    """Execute direct multi-metric assessment over structured input."""
    try:
        output = await default_reasoning_engine.evaluate_async(assessment)
        if format and format.lower() in ("text", "markdown", "human", "md"):
            rendered_text = format_conversational_recommendations(output)
            return PlainTextResponse(content=rendered_text, media_type="text/markdown")
        return output
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error evaluating site assessment: {str(e)}",
        )
