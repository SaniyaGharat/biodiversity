"""Clarifying question generator prioritizing missing ecological pillars without repetition."""

from typing import Optional, Tuple, List
from daaruka.reasoning.models import SiteAssessmentInput, GapAnalysisResult


# Priority ranking for ecological pillars to form robust multi-variable recommendations
CATEGORY_PRIORITY = ["soil", "climate", "land_use", "human_impact", "biodiversity"]

CATEGORY_QUESTIONS = {
    "soil": (
        "To provide accurate, tailored recommendations for your land, could you share key soil metrics—such as your "
        "estimated Topsoil Organic Carbon (SOC%), soil pH, or baseline moisture levels?"
    ),
    "climate": (
        "What is the typical climate and precipitation pattern on your land (e.g. semi-arid with low/erratic rainfall, "
        "seasonal drought, or temperature extremes)?"
    ),
    "land_use": (
        "What is the current primary land use or crop system on your land (e.g. monoculture wheat, mixed cropland, "
        "grazing pasture, or orchard)?"
    ),
    "human_impact": (
        "What current management practices are in place on this land (e.g. conventional intensive plowing vs. reduced tillage, "
        "synthetic fertilizer/pesticide use)?"
    ),
    "biodiversity": (
        "Which specific biodiversity elements or species groups are you most concerned with or aiming to restore (e.g. native pollinators, "
        "beneficial soil biota, birds, or overall vegetation structure)?"
    ),
}

# Contextual joint questions when multiple core variables are missing simultaneously
MULTI_GAP_QUESTIONS = {
    ("soil", "climate", "land_use"): (
        "To give you ecologically grounded recommendations for your land, could you share a few key details: "
        "What is your current land use (e.g. crop type), your local climate/rainfall pattern, and your topsoil organic carbon (SOC%) or soil condition?"
    ),
    ("soil", "climate"): (
        "To assess your site accurately, could you share your baseline soil organic carbon (SOC%) or soil condition, "
        "as well as your local rainfall/climate patterns?"
    ),
}


def select_clarifying_question(
    assessment: SiteAssessmentInput,
    gap_result: GapAnalysisResult,
    asked_categories: List[str],
) -> Optional[Tuple[str, str]]:
    """Select a single prioritized clarifying question for the most critical missing ecological category.
    
    Returns (category_name, question_string) or None if all categories have been asked or gaps are minimal.
    """
    missing = [cat for cat in gap_result.missing_categories if cat not in asked_categories]

    if not missing:
        return None

    # Check for joint missing multi-gap question on first turn if major pillars are missing
    if not asked_categories:
        if "soil" in missing and "climate" in missing and "land_use" in missing:
            return ("composite_site_baseline", MULTI_GAP_QUESTIONS[("soil", "climate", "land_use")])
        if "soil" in missing and "climate" in missing:
            return ("soil_climate_baseline", MULTI_GAP_QUESTIONS[("soil", "climate")])

    # Otherwise, pick highest priority missing individual category
    for cat in CATEGORY_PRIORITY:
        if cat in missing:
            q_text = CATEGORY_QUESTIONS.get(cat)
            if q_text:
                return (cat, q_text)

    # Fallback to any remaining missing category
    first_missing = missing[0]
    return (first_missing, CATEGORY_QUESTIONS.get(first_missing, f"Could you provide more details regarding {first_missing}?"))
