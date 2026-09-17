"""Multi-Metric Reasoning Engine orchestrating gap analysis, retrieval, cross-variable synthesis, and grounding validation."""

import logging
from typing import Dict, Any, List, Optional, Tuple

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

    def _calculate_confidence_summary(
        self, recommendations: List[Recommendation], gaps: Any
    ) -> Tuple[str, str]:
        """Compute top-level confidence level and explicit scientific rationale."""
        if not recommendations:
            return "low", "Insufficient site constraints and scientific evidence to produce grounded recommendations."

        conf_levels = [r.confidence.lower() for r in recommendations]
        num_missing = len(gaps.missing_categories) if hasattr(gaps, "missing_categories") else 0

        if "low" in conf_levels:
            overall = "low"
        elif "medium" in conf_levels or num_missing > 2:
            overall = "medium"
        else:
            overall = "high"

        rationale = (
            f"Overall assessment confidence is rated {overall.upper()} based on {len(recommendations)} peer-reviewed "
            f"action(s) with verified page-level citations from FAO/IPCC/CBD literature and {num_missing} missing ecological pillar(s)."
        )
        return overall, rationale

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
        """Execute synchronous multi-metric evaluation over a site assessment with transparent provenance."""
        working_assessment = assessment.model_copy(deep=True)
        data_provenance: Dict[str, str] = {}

        # 1. Tag initial user-provided fields
        for field, val in working_assessment.model_dump(exclude_none=True).items():
            data_provenance[field] = "user-provided"

        # 2. Auto-enrichment from observational connectors if coordinates exist
        enriched_data: Optional[Dict[str, Any]] = None
        if working_assessment.latitude is not None and working_assessment.longitude is not None:
            enriched_data = {}
            try:
                soil_profile = self.soilgrids_client.get_soil_properties_sync(
                    latitude=working_assessment.latitude, longitude=working_assessment.longitude
                )
                enriched_data["soilgrids"] = soil_profile.model_dump()

                # Auto-populate missing soil metrics from SoilGrids
                if working_assessment.soc_pct is None and soil_profile.soc_g_kg is not None:
                    working_assessment.soc_pct = round(soil_profile.soc_g_kg / 10.0, 2)
                    data_provenance["soc_pct"] = "auto-enriched from SoilGrids (ISRIC 250m REST API)"

                if working_assessment.ph is None and soil_profile.ph_h2o is not None:
                    working_assessment.ph = soil_profile.ph_h2o
                    data_provenance["ph"] = "auto-enriched from SoilGrids (ISRIC 250m REST API)"

                if working_assessment.soil_texture is None and (soil_profile.clay_pct is not None or soil_profile.sand_pct is not None):
                    working_assessment.soil_texture = f"clay {soil_profile.clay_pct}%, sand {soil_profile.sand_pct}%, silt {soil_profile.silt_pct}%"
                    data_provenance["soil_texture"] = "auto-enriched from SoilGrids (ISRIC 250m REST API)"

                if working_assessment.bulk_density_g_cm3 is None and soil_profile.bulk_density_g_cm3 is not None:
                    working_assessment.bulk_density_g_cm3 = soil_profile.bulk_density_g_cm3
                    data_provenance["bulk_density_g_cm3"] = "auto-enriched from SoilGrids (ISRIC 250m REST API)"
            except Exception as e:
                logger.warning(f"Could not sync-enrich from SoilGrids: {e}")

            try:
                bio_metrics = self.gbif_client.get_species_metrics_sync(
                    latitude=working_assessment.latitude, longitude=working_assessment.longitude, radius_km=10.0
                )
                enriched_data["gbif"] = bio_metrics.model_dump()

                # Auto-populate separate species_richness_proxy without overloading biome
                if working_assessment.species_richness_proxy is None:
                    working_assessment.species_richness_proxy = bio_metrics.species_richness_proxy
                    data_provenance["species_richness_proxy"] = (
                        f"auto-enriched from GBIF Occurrence API ({bio_metrics.species_richness_proxy} distinct species across {bio_metrics.total_occurrences_sampled} occurrences)"
                    )
            except Exception as e:
                logger.warning(f"Could not sync-enrich from GBIF: {e}")

        # 3. Gap detection on enriched state (reflecting auto-populated variables)
        gaps = detect_gaps(working_assessment)

        # 4. Targeted knowledge retrieval across multi-topic facets
        queries = generate_targeted_knowledge_queries(working_assessment)
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

        # 5. Cross-variable diagnostic insights
        insights = identify_cross_variable_insights(working_assessment)

        # 6. Synthesize grounded recommendations mapped strictly to retrieved chunks
        candidate_recommendations = self._synthesize_recommendations(working_assessment, available_chunks_map)

        # 7. Strict grounding validation (including numeric presence check)
        validated_recs, validation_log = validate_and_filter_recommendations(
            recommendations=candidate_recommendations,
            available_chunks_map=available_chunks_map,
            strict=False,
            enforce_numeric_grounding=True,
        )

        overall_conf, conf_rationale = self._calculate_confidence_summary(validated_recs, gaps)

        return ReasoningAssessmentOutput(
            site_summary=working_assessment.model_dump(exclude_none=True),
            gap_analysis=gaps,
            enriched_geo_data=enriched_data,
            data_provenance=data_provenance,
            retrieved_evidence_count=len(available_chunks_map),
            cross_variable_insights=insights,
            recommendations=validated_recs,
            overall_confidence=overall_conf,
            confidence_rationale=conf_rationale,
        )

    async def evaluate_async(self, assessment: SiteAssessmentInput) -> ReasoningAssessmentOutput:
        """Asynchronous multi-metric evaluation over a site assessment with auto-enrichment."""
        working_assessment = assessment.model_copy(deep=True)
        data_provenance: Dict[str, str] = {}

        for field, val in working_assessment.model_dump(exclude_none=True).items():
            data_provenance[field] = "user-provided"

        enriched_data: Optional[Dict[str, Any]] = None
        if working_assessment.latitude is not None and working_assessment.longitude is not None:
            enriched_data = {}
            try:
                soil_profile = await self.soilgrids_client.get_soil_properties(
                    latitude=working_assessment.latitude, longitude=working_assessment.longitude
                )
                enriched_data["soilgrids"] = soil_profile.model_dump()

                if working_assessment.soc_pct is None and soil_profile.soc_g_kg is not None:
                    working_assessment.soc_pct = round(soil_profile.soc_g_kg / 10.0, 2)
                    data_provenance["soc_pct"] = "auto-enriched from SoilGrids (ISRIC 250m REST API)"

                if working_assessment.ph is None and soil_profile.ph_h2o is not None:
                    working_assessment.ph = soil_profile.ph_h2o
                    data_provenance["ph"] = "auto-enriched from SoilGrids (ISRIC 250m REST API)"

                if working_assessment.soil_texture is None and (soil_profile.clay_pct is not None or soil_profile.sand_pct is not None):
                    working_assessment.soil_texture = f"clay {soil_profile.clay_pct}%, sand {soil_profile.sand_pct}%, silt {soil_profile.silt_pct}%"
                    data_provenance["soil_texture"] = "auto-enriched from SoilGrids (ISRIC 250m REST API)"

                if working_assessment.bulk_density_g_cm3 is None and soil_profile.bulk_density_g_cm3 is not None:
                    working_assessment.bulk_density_g_cm3 = soil_profile.bulk_density_g_cm3
                    data_provenance["bulk_density_g_cm3"] = "auto-enriched from SoilGrids (ISRIC 250m REST API)"
            except Exception as e:
                logger.warning(f"Could not enrich from SoilGrids: {e}")

            try:
                bio_metrics = await self.gbif_client.get_species_metrics(
                    latitude=working_assessment.latitude, longitude=working_assessment.longitude, radius_km=10.0
                )
                enriched_data["gbif"] = bio_metrics.model_dump()

                if working_assessment.species_richness_proxy is None:
                    working_assessment.species_richness_proxy = bio_metrics.species_richness_proxy
                    data_provenance["species_richness_proxy"] = (
                        f"auto-enriched from GBIF Occurrence API ({bio_metrics.species_richness_proxy} distinct species across {bio_metrics.total_occurrences_sampled} occurrences)"
                    )
            except Exception as e:
                logger.warning(f"Could not enrich from GBIF: {e}")

        gaps = detect_gaps(working_assessment)
        queries = generate_targeted_knowledge_queries(working_assessment)
        available_chunks_map: Dict[str, RetrievedChunk] = {}

        for query_text, tags in queries:
            results = retrieve(query=query_text, top_k=4, filter_tags=tags)
            for chunk in results:
                if chunk.chunk_id not in available_chunks_map:
                    available_chunks_map[chunk.chunk_id] = chunk

        if len(available_chunks_map) < 3:
            broad_results = retrieve(query="cover cropping soil carbon agroforestry restoration", top_k=6)
            for chunk in broad_results:
                available_chunks_map[chunk.chunk_id] = chunk

        insights = identify_cross_variable_insights(working_assessment)
        candidate_recommendations = self._synthesize_recommendations(working_assessment, available_chunks_map)

        validated_recs, validation_log = validate_and_filter_recommendations(
            recommendations=candidate_recommendations,
            available_chunks_map=available_chunks_map,
            strict=False,
            enforce_numeric_grounding=True,
        )

        overall_conf, conf_rationale = self._calculate_confidence_summary(validated_recs, gaps)

        return ReasoningAssessmentOutput(
            site_summary=working_assessment.model_dump(exclude_none=True),
            gap_analysis=gaps,
            enriched_geo_data=enriched_data,
            data_provenance=data_provenance,
            retrieved_evidence_count=len(available_chunks_map),
            cross_variable_insights=insights,
            recommendations=validated_recs,
            overall_confidence=overall_conf,
            confidence_rationale=conf_rationale,
        )

    def _synthesize_recommendations(
        self, assessment: SiteAssessmentInput, available_chunks_map: Dict[str, RetrievedChunk]
    ) -> List[Recommendation]:
        """Synthesize tailored multi-metric recommendations using evidence from retrieved chunks."""
        recommendations: List[Recommendation] = []
        chunks_list = list(available_chunks_map.values())

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

        # Categorize retrieved chunks
        ipcc_forest_chunks = [
            c for c in chunks_list if "ipcc" in c.citation.publisher.lower() and ("conservation" in c.content.lower() or "deforestation" in c.content.lower() or "ecosystem" in c.content.lower())
        ]
        cbd_policy_chunks = [
            c for c in chunks_list if "cbd" in c.citation.publisher.lower()
        ]
        fao_agroforestry_chunks = [
            c for c in chunks_list if "fao" in c.citation.publisher.lower() and ("agroforestry" in c.content.lower() or "agroecological" in c.content.lower() or "tree" in c.content.lower())
        ]
        fao_grassland_chunks = [
            c for c in chunks_list if "fao" in c.citation.publisher.lower() and ("grazing" in c.content.lower() or "pasture" in c.content.lower() or "grassland" in c.content.lower())
        ]
        fao_cover_crop_chunks = [
            c for c in chunks_list if "fao" in c.citation.publisher.lower() and ("cover cropping" in c.content.lower() or "cover crops" in c.content.lower())
        ]
        fao_tillage_chunks = [
            c for c in chunks_list if "fao" in c.citation.publisher.lower() and ("no-till" in c.content.lower() or "tillage" in c.content.lower() or "conventional" in c.content.lower())
        ]

        def _to_source(c: RetrievedChunk) -> RecommendationSource:
            return RecommendationSource(
                chunk_id=c.chunk_id,
                document_title=c.citation.document_title,
                publisher=c.citation.publisher,
                year=c.citation.year,
                section_title=c.citation.section_title,
                page=c.citation.page,
                url_or_doi=c.citation.url_or_doi,
                citation=c.citation.citation_string(),
            )

        # -------------------------------------------------------------
        # Branch A: Tropical Deforestation & Forest Buffer Restoration
        # -------------------------------------------------------------
        if is_tropical or is_deforestation:
            trop_af_sources = []
            if fao_agroforestry_chunks:
                trop_af_sources.append(_to_source(fao_agroforestry_chunks[0]))
            if ipcc_forest_chunks:
                trop_af_sources.append(_to_source(ipcc_forest_chunks[0]))
            elif cbd_policy_chunks:
                trop_af_sources.append(_to_source(cbd_policy_chunks[0]))

            if trop_af_sources:
                recommendations.append(
                    Recommendation(
                        action="Establish Multi-Strata Agroforestry Buffers & High-Carbon Native Tree Corridors",
                        mechanism=(
                            "Establishing multi-layered native tree canopies and agroforestry corridors along deforested margins "
                            "buffers microclimates against thermal extremes, mitigates edge-effect moisture losses, and reconnects "
                            "fragmented habitat patches for native biodiversity."
                        ),
                        variable_interactions=[
                            "Canopy Stratification <-> Microclimate Thermal Buffering",
                            "Forest Buffer Connectivity <-> Native Fauna Dispersal Corridors",
                            "Deep Perennial Root Biomass <-> Humid Tropical Soil Carbon Stabilization",
                        ],
                        impacted_metrics=[
                            "Primary Forest Edge Protection",
                            "Soil Organic Carbon in subsoil layers",
                            "Species Richness Proxy & Forest Connectivity",
                            "Microclimate Stability",
                        ],
                        estimated_effect=(
                            "Protects high-carbon forest margins and enhances structural connectivity per IPCC and FAO agroecological guidelines."
                        ),
                        time_horizon="medium-term",
                        confidence="high",
                        sources=trop_af_sources,
                    )
                )

            trop_cbd_sources = []
            if cbd_policy_chunks:
                trop_cbd_sources.append(_to_source(cbd_policy_chunks[0]))
            if ipcc_forest_chunks:
                trop_cbd_sources.append(_to_source(ipcc_forest_chunks[0]))

            if trop_cbd_sources:
                recommendations.append(
                    Recommendation(
                        action="Targeted Ecological Restoration of Degraded Terrestrial Margins",
                        mechanism=(
                            "Restoring native vegetation cover on degraded agricultural clearings enhances soil hydrological function, "
                            "rebuilds mycorrhizal networks, and halts ongoing carbon emissions from high-carbon terrestrial ecosystems."
                        ),
                        variable_interactions=[
                            "Vegetation Succession <-> Mycorrhizal Network Re-establishment",
                            "Native Reforestation <-> Net Carbon Removals",
                            "Buffer Zone Protection <-> Protected Area Integrity",
                        ],
                        impacted_metrics=[
                            "Ecosystem Intactness & Biodiversity Targets",
                            "Net Biomass Carbon Removals",
                            "Soil Infiltration & Runoff Reduction",
                        ],
                        estimated_effect=(
                            "Advances effective ecological restoration of degraded terrestrial ecosystems to enhance biodiversity and carbon sink capacity."
                        ),
                        time_horizon="long-term",
                        confidence="high",
                        sources=trop_cbd_sources,
                    )
                )

            return recommendations

        # -------------------------------------------------------------
        # Branch B: Temperate Grassland Overgrazing & Pasture Management
        # -------------------------------------------------------------
        if is_grassland or is_overgrazing:
            rot_sources = []
            if fao_grassland_chunks:
                rot_sources.append(_to_source(fao_grassland_chunks[0]))
            elif chunks_list:
                rot_sources.append(_to_source(chunks_list[0]))

            if rot_sources:
                recommendations.append(
                    Recommendation(
                        action="Implement Adaptive Rotational Grazing & Stocking Density Management",
                        mechanism=(
                            "Adjusting livestock grazing frequency, intensity, and paddock rest intervals allows pasture species "
                            "to recover photosynthetic leaf area, preventing topsoil compaction and maintaining root exudation "
                            "essential for soil organic carbon cycling."
                        ),
                        variable_interactions=[
                            "Stocking Density Control <-> Pasture Biomass Regrowth",
                            "Vegetative Cover Preservation <-> Topsoil Macroaggregate Stability",
                            "Root Turnover <-> Grassland Soil Carbon Cycling",
                        ],
                        impacted_metrics=[
                            "Topsoil Carbon Sink Dynamics",
                            "Bulk Density & Soil Compaction",
                            "Pasture Carrying Capacity",
                        ],
                        estimated_effect=(
                            "Maintains positive grassland carbon balance and prevents degradation, optimizing the transition between soil carbon sink and source dynamics."
                        ),
                        time_horizon="short-term",
                        confidence="high",
                        sources=rot_sources,
                    )
                )

            div_sources = []
            if len(fao_grassland_chunks) > 1:
                div_sources.append(_to_source(fao_grassland_chunks[1]))
            elif fao_grassland_chunks:
                div_sources.append(_to_source(fao_grassland_chunks[0]))
            if cbd_policy_chunks:
                div_sources.append(_to_source(cbd_policy_chunks[0]))

            if div_sources:
                recommendations.append(
                    Recommendation(
                        action="Pasture Diversification with Deep-Rooted Perennial Legumes",
                        mechanism=(
                            "Introducing nitrogen-fixing legume species alongside perennial grassland grasses improves soil nitrogen status, "
                            "stimulates deep root development, and enhances soil macroaggregate formation under grazing regimes."
                        ),
                        variable_interactions=[
                            "Legume Nitrogen Fixation <-> Soil Microbiome Activity",
                            "Root Depth Diversity <-> Soil Water & Nutrient Infiltration",
                            "Forage Diversity <-> Grazing Animal Nutrition",
                        ],
                        impacted_metrics=[
                            "Soil Nitrogen Availability & C:N Ratio",
                            "Deep Soil Organic Carbon",
                            "Pasture Floristic Diversity",
                        ],
                        estimated_effect=(
                            "Increases pasture production and soil carbon retention through the incorporation of nitrogen-fixing species and perennial grassland species."
                        ),
                        time_horizon="medium-term",
                        confidence="high",
                        sources=div_sources,
                    )
                )

            return recommendations

        # -------------------------------------------------------------
        # Branch C: Cropland / Semi-Arid Monoculture (Default Regime)
        # -------------------------------------------------------------
        # 1. Recommendation: Agroforestry & Field-Margin Hedgerows
        af_sources = []
        if fao_agroforestry_chunks:
            af_sources.append(_to_source(fao_agroforestry_chunks[0]))
        if cbd_policy_chunks:
            af_sources.append(_to_source(cbd_policy_chunks[0]))
        elif ipcc_forest_chunks:
            af_sources.append(_to_source(ipcc_forest_chunks[0]))

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
                        "landscape heterogeneity, and advances biodiversity-friendly management."
                    ),
                    time_horizon="medium-term",
                    confidence="high",
                    sources=af_sources,
                )
            )

        # 2. Recommendation: Tailored Dryland Cover Cropping & Legume Integration
        cc_sources = []
        if fao_cover_crop_chunks:
            cc_sources.append(_to_source(fao_cover_crop_chunks[0]))
        elif chunks_list:
            cc_sources.append(_to_source(chunks_list[0]))

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
                        "improving water infiltration and aggregate stability."
                    ),
                    time_horizon="short-term",
                    confidence="high",
                    sources=cc_sources,
                )
            )

        # 3. Recommendation: Zero-Tillage Conversion Measured Across Profile (if tillage evidence retrieved)
        if fao_tillage_chunks:
            zt_sources = [_to_source(fao_tillage_chunks[0])]
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
