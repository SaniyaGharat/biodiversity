"""Unit tests for GBIF Occurrence client with mocked HTTP responses."""

import json
from pathlib import Path
from unittest.mock import patch
import pytest

from daaruka.knowledge.connectors.gbif import GBIFClient
from daaruka.knowledge.models import BiodiversityMetrics

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_gbif_json():
    with open(FIXTURES_DIR / "gbif_occurrence_response.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_gbif_parsing_species_richness_proxy(mock_gbif_json):
    """Test GBIF parser calculates species richness proxy, kingdom counts, and IUCN threat detection."""
    client = GBIFClient()
    metrics: BiodiversityMetrics = client._parse_gbif_response(
        raw_data=mock_gbif_json,
        lat=28.6139,
        lon=77.2090,
        radius_km=10.0,
    )

    assert metrics.latitude == 28.6139
    assert metrics.longitude == 77.2090
    assert metrics.search_radius_km == 10.0
    assert metrics.data_source == "Global Biodiversity Information Facility (GBIF)"

    # Total sampled in fixture is 5 occurrences
    assert metrics.total_occurrences_sampled == 5

    # Unique species in fixture: Panthera tigris, Azadirachta indica, Ficus religiosa, Gyps bengalensis = 4
    assert metrics.species_richness_proxy == 4

    # Taxonomic distribution
    assert metrics.taxonomic_distribution.get("Animalia") == 2
    assert metrics.taxonomic_distribution.get("Plantae") == 3

    # Threatened species in fixture: Panthera tigris (EN), Gyps bengalensis (CR) = 2
    assert metrics.threatened_species_count == 2
    threatened_names = [t.scientific_name for t in metrics.threatened_species]
    assert "Panthera tigris" in threatened_names
    assert "Gyps bengalensis" in threatened_names

    # Top observed species
    assert "Azadirachta indica" in metrics.top_observed_species


@pytest.mark.asyncio
async def test_gbif_client_async_mocked(mock_gbif_json):
    """Test async get_species_metrics with mocked HTTP response."""
    client = GBIFClient()

    with patch.object(client, "get_json", return_value=mock_gbif_json) as mock_get:
        metrics = await client.get_species_metrics(latitude=28.6139, longitude=77.2090, radius_km=10.0)

        assert mock_get.called
        assert metrics.species_richness_proxy == 4
        assert metrics.threatened_species_count == 2


def test_bounding_box_calculation():
    """Test coordinate bounding box calculation around Delhi coordinates."""
    client = GBIFClient()
    bbox = client._calculate_bounding_box(lat=28.6139, lon=77.2090, radius_km=10.0)

    assert "decimalLatitude" in bbox
    assert "decimalLongitude" in bbox
    min_lat, max_lat = map(float, bbox["decimalLatitude"].split(","))
    min_lon, max_lon = map(float, bbox["decimalLongitude"].split(","))

    assert min_lat < 28.6139 < max_lat
    assert min_lon < 77.2090 < max_lon
