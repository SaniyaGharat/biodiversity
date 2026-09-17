"""Pydantic data models for Knowledge layer, citations, chunks, and structured connectors."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class SourceCitation(BaseModel):
    """Scientific source citation metadata attached to knowledge chunks."""

    document_title: str = Field(..., description="Full title of the source document or publication")
    publisher: str = Field(..., description="Publishing organization or journal (e.g. FAO, IPCC, IPBES)")
    year: int = Field(..., description="Year of publication")
    section_title: str = Field(default="General", description="Section or chapter heading within the document")
    page: Optional[int] = Field(default=None, description="Page number if applicable")
    topics: List[str] = Field(default_factory=list, description="Categorical ecological topic tags")
    url_or_doi: Optional[str] = Field(default=None, description="URL or DOI identifier for traceability")

    def citation_string(self) -> str:
        """Format standardized scientific citation string."""
        loc = f", Sec. '{self.section_title}'"
        if self.page:
            loc += f" (p. {self.page})"
        doi_str = f" [{self.url_or_doi}]" if self.url_or_doi else ""
        return f"[{self.publisher}, {self.year}] {self.document_title}{loc}{doi_str}"


class RetrievedChunk(BaseModel):
    """Retrieved text chunk with mandatory attached source citation."""

    chunk_id: str = Field(..., description="Unique identifier for the chunk")
    content: str = Field(..., description="Text content of the retrieved chunk")
    similarity_score: float = Field(..., description="Cosine similarity score (0.0 to 1.0)")
    citation: SourceCitation = Field(..., description="Attached source citation")


class KnowledgeSearchResponse(BaseModel):
    """Response payload for knowledge retrieval queries."""

    query: str = Field(..., description="Search query executed")
    total_results: int = Field(..., description="Number of matching chunks returned")
    results: List[RetrievedChunk] = Field(..., description="Retrieved chunks with full citations")


class SoilPropertyLayer(BaseModel):
    """Soil property value for a specific depth interval."""

    depth_interval: str = Field(..., description="Depth range, e.g. '0-5cm', '5-15cm'")
    mean: Optional[float] = Field(default=None, description="Mean property value")
    uncertainty_range: Optional[Dict[str, float]] = Field(
        default=None, description="Confidence interval (e.g. Q0.05 to Q0.95)"
    )


class SoilProfile(BaseModel):
    """Structured soil health metrics from ISRIC SoilGrids."""

    latitude: float
    longitude: float
    soc_g_kg: Optional[float] = Field(default=None, description="Soil Organic Carbon in topsoil (g/kg)")
    soc_stock_t_ha: Optional[float] = Field(default=None, description="Estimated SOC stock (t/ha in 0-30cm)")
    ph_h2o: Optional[float] = Field(default=None, description="Soil pH in H2O solution (standard pH scale 0-14)")
    cec_cmolc_kg: Optional[float] = Field(default=None, description="Cation Exchange Capacity at pH 7 (cmol(c)/kg)")
    clay_pct: Optional[float] = Field(default=None, description="Clay fraction percentage (0-100%)")
    sand_pct: Optional[float] = Field(default=None, description="Sand fraction percentage (0-100%)")
    silt_pct: Optional[float] = Field(default=None, description="Silt fraction percentage (0-100%)")
    bulk_density_g_cm3: Optional[float] = Field(default=None, description="Bulk density of fine earth (g/cm³)")
    depth_layers: Dict[str, List[SoilPropertyLayer]] = Field(
        default_factory=dict, description="Detailed multi-depth property layers"
    )
    data_source: str = Field(default="ISRIC SoilGrids 250m v2.0")


class ThreatenedSpeciesRecord(BaseModel):
    """Record of a threatened or vulnerable species observation."""

    scientific_name: str
    vernacular_name: Optional[str] = None
    iucn_category: str = Field(..., description="IUCN Red List status: CR, EN, VU, NT, LC, DD")
    kingdom: Optional[str] = None
    family: Optional[str] = None
    observation_count: int = 1


class BiodiversityMetrics(BaseModel):
    """Structured biodiversity indicators from GBIF occurrence analysis."""

    latitude: float
    longitude: float
    search_radius_km: float
    species_richness_proxy: int = Field(
        ..., description="Count of distinct scientific species identified in the region"
    )
    total_occurrences_sampled: int = Field(
        ..., description="Total occurrence records analyzed in the bounding area"
    )
    taxonomic_distribution: Dict[str, int] = Field(
        default_factory=dict, description="Occurrence count per taxonomic Kingdom (e.g. Plantae, Animalia)"
    )
    threatened_species_count: int = Field(
        default=0, description="Count of distinct threatened species (CR, EN, VU)"
    )
    threatened_species: List[ThreatenedSpeciesRecord] = Field(
        default_factory=list, description="List of threatened species observed"
    )
    top_observed_species: List[str] = Field(
        default_factory=list, description="Most frequently recorded species names"
    )
    data_source: str = Field(default="Global Biodiversity Information Facility (GBIF)")
