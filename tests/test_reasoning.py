"""Unit and integration tests for Phase 2 Multi-Metric Reasoning Engine."""

import pytest
from pydantic import ValidationError

from daaruka.reasoning.models import (
    SiteAssessmentInput,
    Recommendation,
    RecommendationSource,
)
from daaruka.reasoning.gap_detector import detect_gaps
from daaruka.reasoning.validator import (
    validate_and_filter_recommendations,
    GroundingValidationError,
)
from daaruka.reasoning.engine import evaluate_site, MultiMetricReasoningEngine
from daaruka.knowledge.vector_store import default_vector_store
from daaruka.knowledge.models import RetrievedChunk, SourceCitation


# ---------------------------------------------------------------------------
# 1. GAP DETECTION TESTS
# ---------------------------------------------------------------------------

def test_gap_detection_empty_input():
    """Test gap detector on an empty assessment identifies all 5 categories as missing."""
    empty_input = SiteAssessmentInput()
    gaps = detect_gaps(empty_input)

    assert gaps.data_completeness_score == 0.0
    assert len(gaps.missing_categories) == 5
    assert set(gaps.missing_categories) == {"soil", "land_use", "biodiversity", "climate", "human_impact"}
    assert len(gaps.suggested_clarifications) == 5


def test_gap_detection_partial_input():
    """Test gap detector with only soil and climate parameters supplied."""
    partial_input = SiteAssessmentInput(
        soc_pct=0.4,
        ph=6.5,
        annual_precipitation_mm=400.0,
    )
    gaps = detect_gaps(partial_input)

    assert gaps.data_completeness_score == 0.4  # 2 out of 5
    assert "soil" in gaps.present_categories
    assert "climate" in gaps.present_categories
    assert "land_use" in gaps.missing_categories
    assert "biodiversity" in gaps.missing_categories
    assert "human_impact" in gaps.missing_categories
    assert len(gaps.suggested_clarifications) == 3


def test_gap_detection_full_input():
    """Test gap detector on a fully specified site assessment."""
    full_input = SiteAssessmentInput(
        soc_pct=0.8,
        ph=7.2,
        current_land_use="monoculture wheat",
        biome="semi-arid grassland",
        rainfall_pattern="semi-arid with dry summers",
        tillage_practice="intensive moldboard plowing",
    )
    gaps = detect_gaps(full_input)

    assert gaps.data_completeness_score == 1.0
    assert len(gaps.missing_categories) == 0
    assert len(gaps.present_categories) == 5
    assert len(gaps.suggested_clarifications) == 0


# ---------------------------------------------------------------------------
# 2. GROUNDING & SCHEMA VALIDATOR TESTS
# ---------------------------------------------------------------------------

def test_pydantic_schema_enforces_min_two_variable_interactions():
    """Test Pydantic schema rejects recommendations with fewer than 2 variable interactions."""
    fake_source = RecommendationSource(
        chunk_id="chunk-123",
        document_title="FAO Report",
        publisher="FAO",
        year=2021,
        section_title="Cover Crops",
        page=45,
        citation="[FAO, 2021] FAO Report",
    )

    with pytest.raises(ValidationError) as excinfo:
        Recommendation(
            action="Single variable action",
            mechanism="Only impacts one variable.",
            variable_interactions=["Soil Carbon"],  # Invalid: only 1 variable
            impacted_metrics=["SOC"],
            estimated_effect="+0.5 t/ha",
            time_horizon="short-term",
            confidence="high",
            sources=[fake_source],
        )

    assert "too_short" in str(excinfo.value) or "at least 2" in str(excinfo.value)


def test_validator_rejects_hallucinated_chunk_id():
    """Test grounding validator rejects recommendations pointing to non-existent chunk IDs."""
    fake_source = RecommendationSource(
        chunk_id="non-existent-uuid-12345",
        document_title="Invented Report",
        publisher="Fake Publisher",
        year=2024,
        section_title="Fake Section",
        page=99,
        citation="[Fake, 2024] Fake Report",
    )
    rec = Recommendation(
        action="Plant trees",
        mechanism="Trees sequester carbon and improve soil biology across boundaries.",
        variable_interactions=["Soil Carbon <-> Tree Biomass", "Microclimate <-> Soil Moisture"],
        impacted_metrics=["SOC", "Moisture"],
        estimated_effect="+1.0 t/ha",
        time_horizon="medium-term",
        confidence="high",
        sources=[fake_source],
    )

    available_chunks_map = {}  # Empty retrieved set

    valid_recs, error_log = validate_and_filter_recommendations(
        recommendations=[rec],
        available_chunks_map=available_chunks_map,
        strict=False,
    )

    assert len(valid_recs) == 0
    assert len(error_log) > 0
    assert "Ungrounded chunk_id" in error_log[0]


def test_validator_accepts_grounded_recommendation():
    """Test validator passes recommendations where chunk_id exists in retrieved set."""
    real_chunk = RetrievedChunk(
        chunk_id="real-chunk-uuid-1",
        content="Cover crops increase soil organic carbon stocks.",
        similarity_score=0.92,
        citation=SourceCitation(
            document_title="Recarbonizing Global Soils Vol 3",
            publisher="FAO",
            year=2021,
            section_title="Cover Cropping",
            page=21,
            topics=["soil", "carbon"],
            url_or_doi="https://doi.org/10.4060/cb6595en",
        ),
    )
    available_chunks_map = {"real-chunk-uuid-1": real_chunk}

    src = RecommendationSource(
        chunk_id="real-chunk-uuid-1",
        document_title="Recarbonizing Global Soils Vol 3",
        publisher="FAO",
        year=2021,
        section_title="Cover Cropping",
        page=21,
        citation="[FAO, 2021] Recarbonizing Global Soils Vol 3",
    )

    rec = Recommendation(
        action="Legume Cover Cropping",
        mechanism="Fixes nitrogen to optimize C:N ratio and stabilize carbon in MAOM.",
        variable_interactions=["Nitrogen Fixation <-> Soil Carbon Stabilization", "Ground Cover <-> Soil Moisture"],
        impacted_metrics=["SOC", "Water retention"],
        estimated_effect="+0.32 to +0.55 t C/ha/yr",
        time_horizon="short-term",
        confidence="high",
        sources=[src],
    )

    valid_recs, error_log = validate_and_filter_recommendations(
        recommendations=[rec],
        available_chunks_map=available_chunks_map,
        strict=True,
    )

    assert len(valid_recs) == 1
    assert len(error_log) == 0
    assert valid_recs[0].sources[0].page == 21


# ---------------------------------------------------------------------------
# 3. BENCHMARK INTEGRATION REASONING TEST
# ---------------------------------------------------------------------------

def test_benchmark_semi_arid_wheat_reasoning_integration():
    """Integration test on the hackathon benchmark scenario:
    - SOC: 0.3% (severely degraded)
    - Climate: Semi-arid, low rainfall (<350mm/yr)
    - Land Use: Intensive monoculture wheat
    - Tillage: Intensive moldboard plowing
    """
    benchmark_assessment = SiteAssessmentInput(
        soc_pct=0.3,
        ph=6.8,
        moisture_level="arid",
        current_land_use="monoculture wheat",
        cropping_pattern="continuous monoculture with bare summer fallow",
        rainfall_pattern="semi-arid with low rainfall (<350mm/yr)",
        annual_precipitation_mm=320.0,
        biome="semi-arid dryland / degraded agricultural steppe",
        tillage_practice="intensive moldboard plowing",
    )

    output = evaluate_site(benchmark_assessment)

    # 1. Verify general output structure
    assert output is not None
    assert output.gap_analysis.data_completeness_score == 1.0
    assert output.retrieved_evidence_count > 0
    assert len(output.recommendations) >= 2

    # 2. Verify recommendations include agroforestry, cover cropping / intercropping, or residue management
    rec_actions_text = " ".join(r.action.lower() for r in output.recommendations)
    assert any(term in rec_actions_text for term in ["agroforestry", "hedgerow", "cover crop", "zero-till", "residue"])

    # 3. Verify cross-variable interaction guarantees
    for rec in output.recommendations:
        assert len(rec.variable_interactions) >= 2, f"Recommendation '{rec.action}' must cite >= 2 variable interactions"
        assert len(rec.impacted_metrics) >= 1
        assert rec.estimated_effect != ""
        assert rec.time_horizon in ["short-term", "medium-term", "long-term"]
        assert rec.confidence in ["low", "medium", "high"]

        # 4. Verify grounding & citation traceability
        assert len(rec.sources) >= 1
        for src in rec.sources:
            # Check chunk exists in ChromaDB collection
            res = default_vector_store.collection.get(ids=[src.chunk_id])
            assert len(res["ids"]) == 1, f"Cited chunk_id '{src.chunk_id}' does not exist in ChromaDB!"
            # Check that page number is a real positive integer from the PDF
            assert src.page is not None and src.page > 0, f"Source in '{rec.action}' missing real PDF page number"
            assert src.publisher in [
                "Food and Agriculture Organization of the United Nations (FAO)",
                "Intergovernmental Panel on Climate Change (IPCC)",
                "Convention on Biological Diversity (CBD / UNEP)",
            ]
