"""Pydantic data models for Site Assessment, Gap Analysis, and Multi-Metric Recommendations."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class SiteAssessmentInput(BaseModel):
    """Input parameters representing site-specific ecological and land management conditions.
    All fields are optional to allow robust processing of partial or progressive inputs.
    """

    # 1. Soil Health Metrics
    soc_pct: Optional[float] = Field(default=None, description="Soil Organic Carbon percentage (e.g. 0.3% or 1.5%)")
    ph: Optional[float] = Field(default=None, description="Soil pH value in H2O solution (0.0 to 14.0)")
    moisture_level: Optional[str] = Field(
        default=None, description="Soil moisture regime (e.g. 'arid', 'low', 'moderate', 'saturated')"
    )
    soil_texture: Optional[str] = Field(
        default=None, description="Soil texture class (e.g. 'sandy loam', 'clay', 'silt loam')"
    )
    bulk_density_g_cm3: Optional[float] = Field(default=None, description="Soil bulk density in g/cm³")

    # 2. Land Use & Management
    current_land_use: Optional[str] = Field(
        default=None, description="Current land use (e.g. 'monoculture wheat', 'intensive pasture', 'agroforestry')"
    )
    target_land_use: Optional[str] = Field(
        default=None, description="Target ecological or production objective (e.g. 'regenerative grain', 'restoration')"
    )
    management_goals: Optional[str] = Field(
        default=None, description="Ecological restoration, soil health, or conservation goals"
    )
    area_ha: Optional[float] = Field(default=None, description="Total land area in hectares")
    cropping_pattern: Optional[str] = Field(
        default=None, description="Cropping pattern (e.g. 'continuous monoculture', '2-crop rotation', 'fallow-wheat')"
    )

    # 3. Climate & Water Factors
    rainfall_pattern: Optional[str] = Field(
        default=None, description="Precipitation regime (e.g. 'semi-arid', 'seasonal monsoonal', 'low rainfall <400mm')"
    )
    annual_precipitation_mm: Optional[float] = Field(default=None, description="Mean annual precipitation in mm")
    temperature_regime: Optional[str] = Field(
        default=None, description="Thermal regime (e.g. 'high summer heat >40C', 'frost risk in winter', 'temperate')"
    )
    annual_mean_temp_c: Optional[float] = Field(default=None, description="Mean annual temperature in degrees Celsius")

    # 4. Region & Biome Context
    region: Optional[str] = Field(default=None, description="Geographic region, country, or state")
    biome: Optional[str] = Field(
        default=None, description="Ecosystem/biome classification (e.g. 'semi-arid grassland', 'tropical dry forest')"
    )
    elevation_m: Optional[float] = Field(default=None, description="Elevation above sea level in meters")

    # 5. Human Impact & Farm Practices
    tillage_practice: Optional[str] = Field(
        default=None, description="Tillage method (e.g. 'intensive moldboard plowing', 'reduced till', 'zero-till')"
    )
    chemical_inputs: Optional[str] = Field(
        default=None, description="Fertilizer/pesticide intensity (e.g. 'high synthetic NPK', 'low input', 'organic')"
    )
    irrigation_type: Optional[str] = Field(
        default=None, description="Irrigation infrastructure (e.g. 'rainfed only', 'flood irrigation', 'drip')"
    )
    grazing_intensity: Optional[str] = Field(
        default=None, description="Livestock grazing pressure (e.g. 'heavy continuous', 'rotational', 'none')"
    )

    # Regional Biodiversity Indicator (User-provided or auto-enriched from GBIF)
    species_richness_proxy: Optional[int] = Field(
        default=None, description="Observed or auto-enriched regional species count proxy"
    )

    # Geospatial Coordinates (Optional auto-connector enrichment)
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0, description="Longitude coordinate")


class GapAnalysisResult(BaseModel):
    """Evaluation of missing vs present ecological variable categories."""

    missing_categories: List[str] = Field(
        ..., description="List of missing ecological pillars from ['soil', 'land_use', 'biodiversity', 'climate', 'human_impact']"
    )
    present_categories: List[str] = Field(
        ..., description="List of adequately specified ecological categories"
    )
    data_completeness_score: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of required categories present (0.0 to 1.0)"
    )
    suggested_clarifications: List[str] = Field(
        default_factory=list, description="Targeted follow-up questions to request missing parameters"
    )


class RecommendationSource(BaseModel):
    """Source provenance linking a recommendation to an exact retrieved knowledge chunk."""

    chunk_id: str = Field(..., description="Unique ID of the retrieved chunk in ChromaDB")
    document_title: str = Field(..., description="Title of the source report or publication")
    publisher: str = Field(..., description="Organization (e.g. FAO, IPCC, CBD)")
    year: int = Field(..., description="Year of publication")
    section_title: str = Field(..., description="Section or chapter heading")
    page: Optional[int] = Field(default=None, description="Exact PDF page number")
    url_or_doi: Optional[str] = Field(default=None, description="DOI or source URL")
    citation: str = Field(..., description="Formatted scientific citation string")


class Recommendation(BaseModel):
    """Multi-metric, scientifically grounded ecological recommendation."""

    action: str = Field(..., description="Actionable regenerative or management practice")
    mechanism: str = Field(
        ..., description="Detailed scientific explanation of how and why the practice works across variable interactions"
    )
    variable_interactions: List[str] = Field(
        ...,
        min_length=2,
        description="Explicit list of at least 2 interacting variables (e.g. ['Soil Organic Carbon', 'Soil Moisture Retention'])",
    )
    impacted_metrics: List[str] = Field(
        ..., description="Ecological and agronomic metrics impacted by this intervention"
    )
    estimated_effect: str = Field(
        ..., description="Quantitative expected effect with verifiable numbers derived from retrieved scientific evidence"
    )
    time_horizon: Literal["short-term", "medium-term", "long-term"] = Field(
        ..., description="Time horizon: short-term (<1 yr), medium-term (1-5 yrs), or long-term (>5 yrs)"
    )
    confidence: Literal["low", "medium", "high"] = Field(
        ..., description="Confidence level based on consensus in retrieved evidence and site match"
    )
    sources: List[RecommendationSource] = Field(
        ..., min_length=1, description="List of exact peer-reviewed source chunks supporting this recommendation"
    )


class ReasoningAssessmentOutput(BaseModel):
    """Complete multi-metric reasoning evaluation payload."""

    site_summary: Dict[str, Any] = Field(..., description="Normalized summary of user-provided site parameters")
    gap_analysis: GapAnalysisResult = Field(..., description="Diagnostic of present vs missing variable categories")
    enriched_geo_data: Optional[Dict[str, Any]] = Field(
        default=None, description="Observational data fetched from SoilGrids and GBIF if coordinates were supplied"
    )
    data_provenance: Dict[str, str] = Field(
        default_factory=dict,
        description="Explicit provenance mapping for each field (e.g. 'user-provided', 'auto-enriched from SoilGrids')",
    )
    overall_confidence: Literal["low", "medium", "high"] = Field(
        default="high", description="Overall synthesis confidence score"
    )
    confidence_rationale: str = Field(
        default="", description="Detailed narrative explaining overall confidence level and scientific grounding basis"
    )
    retrieved_evidence_count: int = Field(
        ..., description="Total scientific chunks retrieved and evaluated from the vector base"
    )
    cross_variable_insights: List[str] = Field(
        default_factory=list, description="Synthesis of key multi-metric ecological dynamics identified"
    )
    recommendations: List[Recommendation] = Field(
        ..., description="List of multi-metric, grounded recommendations with verified source citations"
    )
