"""Ecological heuristics, multi-metric interaction definitions, and targeted query generators."""

from typing import List, Dict, Any, Tuple
from daaruka.reasoning.models import SiteAssessmentInput


def generate_targeted_knowledge_queries(assessment: SiteAssessmentInput) -> List[Tuple[str, List[str]]]:
    """Generate multi-topic search queries tailored to the specific combinations of site constraints."""
    queries: List[Tuple[str, List[str]]] = []

    is_semi_arid = any(
        "semi-arid" in str(val).lower() or "arid" in str(val).lower() or "low" in str(val).lower()
        for val in (assessment.rainfall_pattern, assessment.biome, assessment.moisture_level)
    ) or (assessment.annual_precipitation_mm is not None and assessment.annual_precipitation_mm < 500)

    is_low_soc = (assessment.soc_pct is not None and assessment.soc_pct < 1.0) or (
        assessment.moisture_level == "arid"
    )

    is_monoculture = any(
        "monoculture" in str(val).lower() or "wheat" in str(val).lower()
        for val in (assessment.current_land_use, assessment.cropping_pattern)
    )

    is_intensive_tillage = any(
        "intensive" in str(val).lower() or "plow" in str(val).lower() or "tillage" in str(val).lower()
        for val in (assessment.tillage_practice,)
    )

    is_tropical = any(
        "tropical" in str(val).lower() or "humid" in str(val).lower() or "rainforest" in str(val).lower()
        for val in (assessment.rainfall_pattern, assessment.biome, assessment.current_land_use)
    )

    is_deforestation = any(
        "deforest" in str(val).lower() or "clear" in str(val).lower() or "buffer" in str(val).lower() or "logging" in str(val).lower()
        for val in (assessment.current_land_use, assessment.management_goals, assessment.cropping_pattern)
    )

    is_grassland = any(
        "grassland" in str(val).lower() or "pasture" in str(val).lower() or "rangeland" in str(val).lower() or "grazing" in str(val).lower()
        for val in (assessment.biome, assessment.current_land_use, assessment.cropping_pattern)
    )

    is_overgrazing = any(
        "overgraz" in str(val).lower() or "intensive grazing" in str(val).lower() or "stocking" in str(val).lower() or "pasture" in str(val).lower()
        for val in (assessment.current_land_use, assessment.management_goals, assessment.tillage_practice)
    )

    # 1. Tropical Deforestation & Forest Buffer Restoration Query
    if is_tropical or is_deforestation:
        queries.append((
            "tropical deforestation forest restoration biodiversity carbon buffer protected areas high-carbon ecosystems",
            ["biodiversity-targets", "climate", "forest"],
        ))
        queries.append((
            "agroforestry tree biomass carbon sequestration biodiversity corridors",
            ["agriculture", "carbon", "soil"],
        ))

    # 2. Grassland Grazing & Rangeland Management Query
    if is_grassland or is_overgrazing:
        queries.append((
            "Grazing practices frequency and intensity of biomass removals soil structure carbon sink source",
            ["soil", "carbon", "grassland"],
        ))
        queries.append((
            "grassland diversification nitrogen-fixing species perennial grassland species soil conservation",
            ["soil", "agriculture"],
        ))

    # 3. Cover Cropping & Water Dynamics Query (Cropland / Semi-Arid)
    if is_semi_arid and (is_low_soc or is_monoculture):
        queries.append((
            "cover cropping soil organic carbon semi arid water competition agroecological",
            ["soil", "carbon", "cover-cropping"],
        ))
    elif not is_grassland and not is_tropical:
        queries.append((
            "cover cropping organic carbon sequestration rates",
            ["soil", "carbon"],
        ))

    # 4. Agroforestry, Intercropping & Microclimate Query
    if (is_monoculture or is_semi_arid) and not (is_tropical or is_deforestation):
        queries.append((
            "agroforestry intercropping soil carbon moisture retention crop diversification",
            ["agriculture", "carbon", "soil"],
        ))

    # 5. Conservation Tillage & Aggregate Stability Query
    if is_intensive_tillage or (is_low_soc and not is_grassland):
        queries.append((
            "conservation tillage zero-till residue retention soil organic carbon macroaggregates",
            ["soil", "tillage", "carbon"],
        ))

    # 6. Biodiversity Restoration & Ecosystem Resilience Policy Query
    queries.append((
        "ecosystem restoration sustainable agriculture biodiversity connectivity target Kunming Montreal",
        ["policy", "restoration", "biodiversity-targets"],
    ))

    return queries


def identify_cross_variable_insights(assessment: SiteAssessmentInput) -> List[str]:
    """Generate diagnostic insights highlighting interactions between site variables."""
    insights: List[str] = []

    # Interaction: SOC <-> Water Retention <-> Aridity
    if (assessment.soc_pct is not None and assessment.soc_pct < 0.8) and (
        "semi-arid" in str(assessment.rainfall_pattern).lower()
        or (assessment.annual_precipitation_mm and assessment.annual_precipitation_mm < 500)
    ):
        insights.append(
            "Coupled Soil-Climate Vulnerability: Depleted topsoil carbon (< 0.8% SOC) drastically reduces soil water "
            "holding capacity in a semi-arid climate, exacerbating moisture deficit during dry periods and promoting surface crusting."
        )

    # Interaction: Monoculture <-> Biodiversity Deficit <-> Soil Biological Activity
    if assessment.current_land_use and "monoculture" in assessment.current_land_use.lower():
        insights.append(
            "Land-Use & Biodiversity Depletion: Continuous monoculture production eliminates floral heterogeneity, "
            "impairing native pollinator communities and starving the soil microbiome of diverse root exudates essential for organic matter stabilization."
        )

    # Interaction: Intensive Tillage <-> Carbon Mineralization
    if assessment.tillage_practice and (
        "intensive" in assessment.tillage_practice.lower() or "plow" in assessment.tillage_practice.lower()
    ):
        insights.append(
            "Management & Soil Aggregate Disruption: Intensive mechanical tillage physically fractures soil macroaggregates, "
            "exposing previously protected particulate organic carbon to rapid microbial oxidation and evaporative moisture loss."
        )

    # Interaction: Tropical Deforestation <-> High-Carbon Biomass Loss <-> Buffer Fragmentation
    if any(
        "tropical" in str(val).lower() or "humid" in str(val).lower() or "deforest" in str(val).lower()
        for val in (assessment.rainfall_pattern, assessment.biome, assessment.current_land_use)
    ):
        insights.append(
            "Tropical Carbon-Biodiversity Nexus: Agricultural clearing of primary tropical forest causes immediate loss "
            "of high-carbon biomass and disrupts structural buffer zones, converting protected forest margins into net carbon sources (IPCC AR6 WGII Ch 2)."
        )

    # Interaction: Grassland Overgrazing <-> Pasture Biomass & Carbon Dynamics
    if any(
        "grassland" in str(val).lower() or "pasture" in str(val).lower() or "grazing" in str(val).lower()
        for val in (assessment.biome, assessment.current_land_use, assessment.cropping_pattern)
    ):
        insights.append(
            "Grassland Grazing Intensity & Carbon Balance: Continuous unmanaged stocking pressure depletes vegetative cover "
            "and accelerates soil structural degradation, turning grassland soils from potential carbon sinks into net emissions sources (FAO Vol 3 p. 418)."
        )

    return insights
