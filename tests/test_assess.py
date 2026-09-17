"""Tests for Phase 4: Direct structured JSON assessment endpoint and geo-coordinate auto-enrichment."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi.testclient import TestClient
from daaruka.main import app
from daaruka.reasoning.models import SiteAssessmentInput, ReasoningAssessmentOutput
from daaruka.reasoning.engine import MultiMetricReasoningEngine
from daaruka.knowledge.models import SoilProfile, BiodiversityMetrics

client = TestClient(app)


def test_assess_endpoint_with_brief_exact_example_json():
    """Unit test /api/v1/assess with full JSON payload matching the brief's example:
    soc_pct 0.3%, low rainfall, monoculture wheat, semi-arid -> returns grounded recommendations directly.
    """
    payload = {
        "soc_pct": 0.3,
        "rainfall_pattern": "low / erratic rainfall with seasonal dry spells",
        "current_land_use": "cropland / monoculture wheat cultivation",
        "biome": "semi-arid",
        "tillage_practice": "intensive conventional inversion tillage",
    }

    response = client.post("/api/v1/assess", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
    assert data["gap_analysis"]["data_completeness_score"] == 1.0
    assert len(data["gap_analysis"]["missing_categories"]) == 0

    # Assert provenance marks all inputs as user-provided
    for field in ["soc_pct", "rainfall_pattern", "current_land_use", "biome", "tillage_practice"]:
        assert data["data_provenance"].get(field) == "user-provided"

    # Assert recommendations have grounded peer-reviewed citations
    for rec in data["recommendations"]:
        assert len(rec["sources"]) >= 1
        for src in rec["sources"]:
            assert src["page"] is not None or src["section_title"] is not None
            assert src["document_title"] != ""


def test_geo_coordinate_auto_enrichment_and_gap_reduction():
    """Integration test: submit ONLY lat/long + land_use via JSON, mock SoilGrids/GBIF,
    assert gap_detector correctly sees soil and biodiversity as satisfied from auto-enrichment.
    """
    mock_soil_profile = SoilProfile(
        latitude=31.5,
        longitude=-100.2,
        soc_g_kg=8.5,  # Converts to 0.85% SOC
        ph_h2o=7.2,
        clay_pct=22.0,
        sand_pct=45.0,
        silt_pct=33.0,
        bulk_density_g_cm3=1.35,
        data_source="ISRIC SoilGrids 250m v2.0",
    )

    mock_bio_metrics = BiodiversityMetrics(
        latitude=31.5,
        longitude=-100.2,
        search_radius_km=10.0,
        total_occurrences_sampled=142,
        species_richness_proxy=48,
        threatened_species=[],
        data_source="GBIF Occurrence API",
    )

    engine = MultiMetricReasoningEngine()
    engine.soilgrids_client.get_soil_properties_sync = MagicMock(return_value=mock_soil_profile)
    engine.gbif_client.get_species_metrics_sync = MagicMock(return_value=mock_bio_metrics)

    minimal_input = SiteAssessmentInput(
        latitude=31.5,
        longitude=-100.2,
        current_land_use="cropland / monoculture wheat",
    )

    output = engine.evaluate(minimal_input)

    # 1. Soil and Biodiversity must be marked present in gap_analysis due to auto-enrichment
    assert "soil" in output.gap_analysis.present_categories
    assert "biodiversity" in output.gap_analysis.present_categories
    assert "land_use" in output.gap_analysis.present_categories

    # 2. Assert auto-populated values
    assert output.site_summary["soc_pct"] == 0.85
    assert output.site_summary["ph"] == 7.2
    assert output.site_summary["bulk_density_g_cm3"] == 1.35

    # 3. Assert transparent provenance mapping
    assert output.data_provenance["current_land_use"] == "user-provided"
    assert output.data_provenance["latitude"] == "user-provided"
    assert output.data_provenance["longitude"] == "user-provided"
    assert "auto-enriched from SoilGrids" in output.data_provenance["ph"]
    assert "auto-enriched from GBIF" in output.data_provenance["species_richness_proxy"]
    assert output.site_summary["species_richness_proxy"] == 48

    # 4. Assert recommendations were produced based on enriched soil context
    assert len(output.recommendations) >= 1


def test_api_assess_endpoint_with_coordinates_live_or_mocked():
    """Verify POST /api/v1/assess endpoint handles coordinate payload and returns data provenance."""
    payload = {
        "latitude": 34.5,
        "longitude": -101.2,
        "current_land_use": "cropland / wheat cultivation",
        "rainfall_pattern": "low / erratic rainfall",
    }

    response = client.post("/api/v1/assess", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert "data_provenance" in data
    assert data["data_provenance"]["current_land_use"] == "user-provided"
    assert "recommendations" in data
    assert len(data["recommendations"]) >= 1
