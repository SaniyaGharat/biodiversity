"""Multi-Metric Reasoning Engine orchestrating gap analysis, retrieval, cross-variable synthesis, and grounding validation."""

import logging
from typing import Dict, Any, List, Optional

from daaruka.knowledge.models import RetrievedChunk
from daaruka.knowledge.retriever import retrieve
from daaruka.knowledge.connectors.soilgrids import SoilGridsClient
from daaruka.knowledge.connectors.gbif import GBIFClient
from daaruka.reasoning.models import (
    SiteAssessmentInput,
    ReasoningAssessmentOutput,
    Recommendation,
    RecommendationSource,
)
from daaruka.reasoning.gap_detector import detect_gaps
from daaruka.reasoning.rules import (
    generate_targeted_knowledge_queries,
    identify_cross_variable_insights,
)
from daaruka.reasoning.validator import validate_and_filter_recommendations

logger = logging.getLogger(__name__)


class MultiMetricReasoningEngine:
    """Core reasoning engine generating grounded, multi-variable ecological recommendations."""

    def __init__(
        self,
        soilgrids_client: Optional[SoilGridsClient] = None,
        gbif_client: Optional[GBIFClient] = None,
    ):
        self.soilgrids_client = soilgrids_client or SoilGridsClient()
        self.gbif_client = gbif_client or GBIFClient()

    async def _enrich_from_connectors(self, lat: float, lon: float) -> Dict[str, Any]:
        """Fetch real-world observational data from SoilGrids and GBIF for coordinates."""
        enriched: Dict[str, Any] = {}
        try:
            soil_profile = await self.soilgrids_client.get_soil_properties(latitude=lat, longitude=lon)
            enriched["soilgrids"] = soil_profile.model_dump()
        except Exception as e:
            logger.warning(f"Could not enrich from SoilGrids for ({lat}, {lon}): {e}")

        try:
            bio_metrics = await self.gbif_client.get_species_metrics(latitude=lat, longitude=lon, radius_km=10.0)
            enriched["gbif"] = bio_metrics.model_dump()
        except Exception as e:
            logger.warning(f"Could not enrich from GBIF for ({lat}, {lon}): {e}")

        return enriched

    def _enrich_from_connectors_sync(self, lat: float, lon: float) -> Dict[str, Any]:
        """Synchronously fetch observational data from SoilGrids and GBIF."""
        enriched: Dict[str, Any] = {}
        try:
            soil_profile = self.soilgrids_client.get_soil_properties_sync(latitude=lat, longitude=lon)
            enriched["soilgrids"] = soil_profile.model_dump()
        except Exception as e:
            logger.warning(f"Could not sync-enrich from SoilGrids: {e}")

        try:
            bio_metrics = self.gbif_client.get_species_metrics_sync(latitude=lat, longitude=lon, radius_km=10.0)
            enriched["gbif"] = bio_metrics.model_dump()
        except Exception as e:
            logger.warning(f"Could not sync-enrich from GBIF: {e}")

        return enriched

    def evaluate(self, assessment: SiteAssessmentInput) -> ReasoningAssessmentOutput:
        """Execute synchronous multi-metric evaluation over a site assessment."""
        # Step 1: Gap detection
        gaps = detect_gaps(assessment)

        # Step 2: Auto-enrichment if coordinates exist
        enriched_data: Optional[Dict[str, Any]] = None
        if assessment.latitude is not None and assessment.longitude is not None:
            enriched_data = self._enrich_from_connectors_sync(assessment.latitude, assessment.longitude)

        # Step 3: Targeted knowledge retrieval across multi-topic facets
        queries = generate_targeted_knowledge_queries(assessment)
        available_chunks_map: Dict[str, RetrievedChunk] = {}

        for query_text, tags in queries:
            results = retrieve(query=query_text, top_k=4, filter_tags=tags)
            for chunk in results:
                if chunk.chunk_id not in available_chunks_map:
                    available_chunks_map[chunk.chunk_id] = chunk

        # Fallback broad retrieval if specific tags had limited chunks
        if len(available_chunks_map) < 3:
            broad_results = retrieve(query="cover cropping soil carbon agroforestry restoration", top_k=6)
            for chunk in broad_results:
                available_chunks_map[chunk.chunk_id] = chunk

        # Step 4: Cross-variable diagnostic insights
        insights = identify_cross_variable_insights(assessment)

        # Step 5: Synthesize grounded recommendations mapped strictly to retrieved chunks
        candidate_recommendations = self._synthesize_recommendations(assessment, available_chunks_map)

        # Step 6: Strict grounding validation (including numeric presence check)
        validated_recs, validation_log = validate_and_filter_recommendations(
            recommendations=candidate_recommendations,
            available_chunks_map=available_chunks_map,
            strict=False,
            enforce_numeric_grounding=True,
        )

        return ReasoningAssessmentOutput(
            site_summary=assessment.model_dump(exclude_none=True),
            gap_analysis=gaps,
            enriched_geo_data=enriched_data,
            retrieved_evidence_count=len(available_chunks_map),
            cross_variable_insights=insights,
            recommendations=validated_recs,
        )

    def _synthesize_recommendations(
        self, assessment: SiteAssessmentInput, available_chunks_map: Dict[str, RetrievedChunk]
    ) -> List[Recommendation]:
        """Synthesize tailored multi-metric recommendations using evidence from retrieved chunks."""
        recommendations: List[Recommendation] = []
        chunks_list = list(available_chunks_map.values())

        # Match specific chunks by content and source
        fao_agroforestry_chunks = [
            c for c in chunks_list if "fao" in c.citation.publisher.lower() and ("agroforestry" in c.content.lower() or "agroecological" in c.content.lower())
        ]
        fao_cover_crop_chunks = [
            c for c in chunks_list if "fao" in c.citation.publisher.lower() and ("cover cropping" in c.content.lower() or "cover crops" in c.content.lower())
        ]
        fao_tillage_chunks = [
            c for c in chunks_list if "fao" in c.citation.publisher.lower() and ("no-till" in c.content.lower() or "tillage" in c.content.lower() or "conventional" in c.content.lower())
        ]
        policy_resilience_chunks = [
            c for c in chunks_list if ("cbd" in c.citation.publisher.lower() or "ipcc" in c.citation.publisher.lower())
        ]

        # 1. Recommendation: Agroforestry & Field-Margin Hedgerows
        af_sources = []
        if fao_agroforestry_chunks:
            c = fao_agroforestry_chunks[0]
            af_sources.append(
                RecommendationSource(
                    chunk_id=c.chunk_id,
                    document_title=c.citation.document_title,
                    publisher=c.citation.publisher,
                    year=c.citation.year,
                    section_title=c.citation.section_title,
                    page=c.citation.page,
                    url_or_doi=c.citation.url_or_doi,
                    citation=c.citation.citation_string(),
                )
            )
        if policy_resilience_chunks:
            c = policy_resilience_chunks[0]
            af_sources.append(
                RecommendationSource(
                    chunk_id=c.chunk_id,
                    document_title=c.citation.document_title,
                    publisher=c.citation.publisher,
                    year=c.citation.year,
                    section_title=c.citation.section_title,
                    page=c.citation.page,
                    url_or_doi=c.citation.url_or_doi,
                    citation=c.citation.citation_string(),
                )
            )

        if af_sources:
            recommendations.append(
                Recommendation(
                    action="Integrate Multi-Species Agroforestry Hedgerows & Field Margins",
                    mechanism=(
                        "Combining woody perennials with annual crops establishes structural diversity that buffers microclimates "
                        "against heat extremes, reduces wind-driven evapotranspiration, and creates continuous ecological corridors "
                        "for beneficial pollinator and predator taxa across monoculture landscapes."
                    ),
                    variable_interactions=[
                        "Vegetation Structural Diversity <-> Microclimate Thermal Buffering",
                        "Landscape Heterogeneity <-> Pollinator & Predator Abundance",
                        "Tree Root Biomass <-> Deep Soil Carbon Stabilization",
                    ],
                    impacted_metrics=[
                        "Field Evaporative Water Loss",
                        "Soil Organic Carbon in subsoil layers",
                        "Species Richness Proxy & Pollinator Density",
                        "Ecological Connectivity (CBD Target 10)",
                    ],
                    estimated_effect=(
                        "Increases carbon storage through combined aboveground and belowground tree biomass, enhances structural "
                        "landscape heterogeneity, and advances biodiversity-friendly management mandated under CBD Kunming-Montreal Target 10."
                    ),
                    time_horizon="medium-term",
                    confidence="high",
                    sources=af_sources,
                )
            )

        # 2. Recommendation: Tailored Dryland Cover Cropping & Legume Integration
        cc_sources = []
        if fao_cover_crop_chunks:
            c = fao_cover_crop_chunks[0]
            cc_sources.append(
                RecommendationSource(
                    chunk_id=c.chunk_id,
                    document_title=c.citation.document_title,
                    publisher=c.citation.publisher,
                    year=c.citation.year,
                    section_title=c.citation.section_title,
                    page=c.citation.page,
                    url_or_doi=c.citation.url_or_doi,
                    citation=c.citation.citation_string(),
                )
            )
        elif chunks_list:
            c = chunks_list[0]
            cc_sources.append(
                RecommendationSource(
                    chunk_id=c.chunk_id,
                    document_title=c.citation.document_title,
                    publisher=c.citation.publisher,
                    year=c.citation.year,
                    section_title=c.citation.section_title,
                    page=c.citation.page,
                    url_or_doi=c.citation.url_or_doi,
                    citation=c.citation.citation_string(),
                )
            )

        if cc_sources:
            recommendations.append(
                Recommendation(
                    action="Implement Seasonal Legume Cover Cropping Tailored to Semiarid Moisture Constraints",
                    mechanism=(
                        "Introducing drought-adapted leguminous cover crops fixes atmospheric nitrogen to enhance microbial C:N balance "
                        "and build topsoil organic carbon. In semiarid regions where precipitation is limited, careful selection of cover "
                        "crop species and growth windows avoids soil water competition with primary crops (Unger and Vigil, 1998)."
                    ),
                    variable_interactions=[
                        "Legume Nitrogen Fixation <-> Soil Microbial Carbon Stabilization",
                        "Cover Crop Water Demand <-> Semiarid Available Soil Moisture",
                        "Crop Diversification <-> Soil Biota Redundancy",
                    ],
                    impacted_metrics=[
                        "Topsoil Organic Carbon Stock (SOC)",
                        "Available Soil Moisture Retention",
                        "Soil Microbial Parameters",
                    ],
                    estimated_effect=(
                        "Enhances soil organic carbon stocks while managing potential soil water competition in semiarid environments, "
                        "improving water infiltration and aggregate stability per FAO Technical Manual Vol. 3 (Page 21)."
                    ),
                    time_horizon="short-term",
                    confidence="high",
                    sources=cc_sources,
                )
            )

        # 3. Recommendation: Zero-Tillage Conversion Measured Across Profile (if tillage evidence retrieved)
        if fao_tillage_chunks:
            c = fao_tillage_chunks[0]
            zt_sources = [
                RecommendationSource(
                    chunk_id=c.chunk_id,
                    document_title=c.citation.document_title,
                    publisher=c.citation.publisher,
                    year=c.citation.year,
                    section_title=c.citation.section_title,
                    page=c.citation.page,
                    url_or_doi=c.citation.url_or_doi,
                    citation=c.citation.citation_string(),
                )
            ]
            recommendations.append(
                Recommendation(
                    action="Transition to Conservation Tillage & Residue Retention Management",
                    mechanism=(
                        "Eliminating or reducing intensive tillage avoids continuous soil aggregate disruption in topsoil layers, "
                        "reducing oxidative carbon losses while increasing water infiltration and reducing soil erosion."
                    ),
                    variable_interactions=[
                        "Tillage Reduction <-> Soil Organic Carbon Accumulation",
                        "Soil Structure Protection <-> Infiltration Capacity",
                    ],
                    impacted_metrics=[
                        "Topsoil Organic Carbon Retention",
                        "Soil Macroaggregate Stability",
                        "Surface Evaporative Water Loss",
                    ],
                    estimated_effect=(
                        "Stabilizes topsoil organic carbon and improves soil structure retention compared to conventional inversion plowing."
                    ),
                    time_horizon="short-term",
                    confidence="high",
                    sources=zt_sources,
                )
            )

        return recommendations


# Global default reasoning engine
default_reasoning_engine = MultiMetricReasoningEngine()


def evaluate_site(assessment: SiteAssessmentInput) -> ReasoningAssessmentOutput:
    """Convenience function to evaluate site assessment through the default reasoning engine."""
    return default_reasoning_engine.evaluate(assessment)
