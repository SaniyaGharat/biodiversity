"""Final Audit & Multi-Scenario Scientific Grounding Test Suite."""

import pytest
from httpx import AsyncClient, ASGITransport

from daaruka.main import app
from daaruka.reasoning.models import SiteAssessmentInput
from daaruka.reasoning.engine import MultiMetricReasoningEngine
from daaruka.reasoning.validator import verify_numeric_grounding
from daaruka.knowledge.vector_store import default_vector_store


@pytest.fixture
def test_engine():
    return MultiMetricReasoningEngine()


@pytest.mark.asyncio
async def test_scenario_1_semiarid_cropland(test_engine):
    """Test Scenario 1: Semi-arid monoculture cropland with low SOC."""
    site = SiteAssessmentInput(
        soc_pct=0.6,
        ph=7.2,
        moisture_level="arid",
        current_land_use="monoculture wheat farming",
        rainfall_pattern="semi-arid",
        annual_precipitation_mm=380.0,
        tillage_practice="intensive moldboard plow",
        biome="semi-arid Mediterranean",
    )
    output = await test_engine.evaluate_async(site)

    assert len(output.recommendations) >= 2
    assert output.overall_confidence in ("high", "medium")
    assert "FAO" in str(output.recommendations[0].sources[0].publisher)

    # Multi-metric variable interactions enforced (>= 2 per recommendation)
    for rec in output.recommendations:
        assert len(rec.variable_interactions) >= 2
        for src in rec.sources:
            chunk_doc = default_vector_store.collection.get(ids=[src.chunk_id])["documents"][0]
            is_valid, violations = verify_numeric_grounding(rec.estimated_effect, chunk_doc)
            assert is_valid is True, f"Numeric grounding violation: {violations}"


@pytest.mark.asyncio
async def test_scenario_2_humid_tropics_deforestation(test_engine):
    """Test Scenario 2: Humid tropics deforestation / forest buffer degradation."""
    site = SiteAssessmentInput(
        soc_pct=2.1,
        ph=4.8,
        moisture_level="humid",
        current_land_use="deforested cattle clearing and crop buffer",
        rainfall_pattern="tropical monsoon humid",
        annual_precipitation_mm=2100.0,
        management_goals="restore forest buffer, prevent edge erosion, connect wildlife corridor",
        biome="tropical moist broadleaf forest",
    )
    output = await test_engine.evaluate_async(site)

    assert len(output.recommendations) >= 2
    assert output.overall_confidence in ("high", "medium")
    assert output.site_summary.get("biome") == "tropical moist broadleaf forest"

    # Verify retrieved citations include IPCC AR6 and/or CBD
    all_publishers = [
        src.publisher for rec in output.recommendations for src in rec.sources
    ]
    assert any("IPCC" in pub or "CBD" in pub or "FAO" in pub for pub in all_publishers)

    # Multi-metric interactions (>= 2 per recommendation)
    for rec in output.recommendations:
        assert len(rec.variable_interactions) >= 2
        for src in rec.sources:
            chunk_doc = default_vector_store.collection.get(ids=[src.chunk_id])["documents"][0]
            is_valid, violations = verify_numeric_grounding(rec.estimated_effect, chunk_doc)
            assert is_valid is True, f"Numeric grounding violation: {violations}"


@pytest.mark.asyncio
async def test_scenario_3_temperate_grassland_overgrazing(test_engine):
    """Test Scenario 3: Temperate grassland overgrazing / pasture degradation."""
    site = SiteAssessmentInput(
        soc_pct=1.8,
        ph=6.5,
        moisture_level="moderate",
        current_land_use="intensive pasture grazing",
        rainfall_pattern="temperate continental",
        annual_precipitation_mm=750.0,
        management_goals="alleviate soil compaction, improve forage resilience, sequester carbon",
        biome="temperate grassland steppe",
    )
    output = await test_engine.evaluate_async(site)

    assert len(output.recommendations) >= 2
    assert output.overall_confidence in ("high", "medium")

    # Verify grassland-specific actions and FAO citations
    action_texts = [rec.action.lower() for rec in output.recommendations]
    assert any("grazing" in act or "pasture" in act for act in action_texts)

    for rec in output.recommendations:
        assert len(rec.variable_interactions) >= 2
        for src in rec.sources:
            chunk_doc = default_vector_store.collection.get(ids=[src.chunk_id])["documents"][0]
            is_valid, violations = verify_numeric_grounding(rec.estimated_effect, chunk_doc)
            assert is_valid is True, f"Numeric grounding violation: {violations}"


@pytest.mark.asyncio
async def test_assess_endpoint_text_format():
    """Test POST /api/v1/assess with ?format=text query param."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "rainfall_pattern": "tropical humid",
            "current_land_use": "deforested clearing",
            "biome": "tropical rainforest",
            "soc_pct": 1.5,
        }
        # 1. Test format=json (default)
        resp_json = await ac.post("/api/v1/assess", json=payload)
        assert resp_json.status_code == 200
        data = resp_json.json()
        assert "recommendations" in data
        assert "overall_confidence" in data
        assert "confidence_rationale" in data

        # 2. Test format=text
        resp_text = await ac.post("/api/v1/assess?format=text", json=payload)
        assert resp_text.status_code == 200
        assert "text/markdown" in resp_text.headers.get("content-type", "")
        text = resp_text.text
        assert "Based on the multi-variable ecological profile" in text
        assert "Overall Assessment Confidence" in text
        assert "Ecological Mechanism" in text
        assert "Cross-Variable Interactions & Synergies" in text
        assert "Scientific Evidence & Citations" in text


@pytest.mark.asyncio
async def test_biome_decoupling_with_geo_enrichment():
    """Verify that GBIF species count populates species_richness_proxy without corrupting biome."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "latitude": 51.5074,
            "longitude": 0.1278,
            "biome": "temperate deciduous forest",
        }
        resp = await ac.post("/api/v1/assess", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        site_summary = data["site_summary"]

        # Biome must remain exactly what the user provided
        assert site_summary["biome"] == "temperate deciduous forest"
        # species_richness_proxy must be populated separately from GBIF
        assert "species_richness_proxy" in site_summary or "species_richness_proxy" in data["data_provenance"]
