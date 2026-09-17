"""Gap detection module to diagnose missing ecological variables and generate clarification prompts."""

from typing import List
from daaruka.reasoning.models import SiteAssessmentInput, GapAnalysisResult


def detect_gaps(assessment: SiteAssessmentInput) -> GapAnalysisResult:
    """Analyze a site assessment across the 5 core ecological pillars and identify missing inputs.

    Pillars evaluated:
    1. Soil Health (SOC, pH, moisture, texture)
    2. Land Use (current crop/use, cropping pattern, area)
    3. Biodiversity & Biome (biome type, native vegetation, habitat structure)
    4. Climate Factors (precipitation pattern, temperature extremes)
    5. Human Impact (tillage, chemical inputs, irrigation, grazing pressure)
    """
    present_categories: List[str] = []
    missing_categories: List[str] = []
    clarification_prompts: List[str] = []

    # 1. Check Soil Health
    has_soil = any(
        val is not None
        for val in (
            assessment.soc_pct,
            assessment.ph,
            assessment.moisture_level,
            assessment.soil_texture,
            assessment.bulk_density_g_cm3,
        )
    )
    if has_soil:
        present_categories.append("soil")
    else:
        missing_categories.append("soil")
        clarification_prompts.append(
            "What is your current topsoil organic carbon (SOC%), soil pH, or baseline moisture level?"
        )

    # 2. Check Land Use
    has_land_use = any(
        val is not None
        for val in (
            assessment.current_land_use,
            assessment.target_land_use,
            assessment.cropping_pattern,
            assessment.area_ha,
        )
    )
    if has_land_use:
        present_categories.append("land_use")
    else:
        missing_categories.append("land_use")
        clarification_prompts.append(
            "What is the current land use or cropping system (e.g. continuous monoculture, crop rotation, pasture)?"
        )

    # 3. Check Biodiversity & Biome Context
    has_biodiversity = any(
        val is not None
        for val in (
            assessment.biome,
            assessment.region,
            assessment.elevation_m,
            assessment.species_richness_proxy,
        )
    )
    if has_biodiversity:
        present_categories.append("biodiversity")
    else:
        missing_categories.append("biodiversity")
        clarification_prompts.append(
            "What ecosystem or biome classification characterizes the region (e.g. semi-arid grassland, Mediterranean, tropical dry)?"
        )

    # 4. Check Climate Factors
    has_climate = any(
        val is not None
        for val in (
            assessment.rainfall_pattern,
            assessment.annual_precipitation_mm,
            assessment.temperature_regime,
            assessment.annual_mean_temp_c,
        )
    )
    if has_climate:
        present_categories.append("climate")
    else:
        missing_categories.append("climate")
        clarification_prompts.append(
            "What are your typical annual precipitation and temperature patterns (e.g. semi-arid with <400mm rainfall, seasonal drought)?"
        )

    # 5. Check Human Impact & Practices
    has_human_impact = any(
        val is not None
        for val in (
            assessment.tillage_practice,
            assessment.chemical_inputs,
            assessment.irrigation_type,
            assessment.grazing_intensity,
        )
    )
    if has_human_impact:
        present_categories.append("human_impact")
    else:
        missing_categories.append("human_impact")
        clarification_prompts.append(
            "What current land management practices are applied (e.g. intensive moldboard plowing vs no-till, synthetic inputs vs organic)?"
        )

    completeness_score = round(len(present_categories) / 5.0, 2)

    return GapAnalysisResult(
        missing_categories=missing_categories,
        present_categories=present_categories,
        data_completeness_score=completeness_score,
        suggested_clarifications=clarification_prompts,
    )
