"""Unit tests for SoilGrids REST client with mocked HTTP responses."""

import json
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
import httpx

from daaruka.knowledge.connectors.soilgrids import SoilGridsClient
from daaruka.knowledge.models import SoilProfile

FIXTURES_DIR = Path(__file__).parent / "fixtures"


@pytest.fixture
def mock_soilgrids_json():
    with open(FIXTURES_DIR / "soilgrids_response.json", "r", encoding="utf-8") as f:
        return json.load(f)


def test_soilgrids_parsing_unit_conversions(mock_soilgrids_json):
    """Test SoilGrids parser standardizes pH, SOC, CEC, texture %, and bulk density."""
    client = SoilGridsClient()
    profile: SoilProfile = client._parse_soilgrids_response(
        raw_data=mock_soilgrids_json,
        lat=28.6139,
        lon=77.2090,
    )

    assert profile.latitude == 28.6139
    assert profile.longitude == 77.2090
    assert profile.data_source == "ISRIC SoilGrids 250m v2.0"

    # Raw 72 (pH*10) -> 7.2
    assert profile.ph_h2o == 7.2

    # Raw 185 dg/kg -> 18.5 g/kg
    assert profile.soc_g_kg == 18.5

    # Raw 210 mmol(c)/kg -> 21.0 cmol(c)/kg
    assert profile.cec_cmolc_kg == 21.0

    # Raw g/kg -> %
    assert profile.clay_pct == 28.0
    assert profile.sand_pct == 45.0
    assert profile.silt_pct == 27.0

    # Raw 138 cg/cm3 -> 1.38 g/cm3
    assert profile.bulk_density_g_cm3 == 1.38

    # Check detailed depth layers
    assert "soc" in profile.depth_layers
    assert len(profile.depth_layers["soc"]) == 2
    assert profile.depth_layers["soc"][0].depth_interval == "0-5cm"
    assert profile.depth_layers["soc"][0].mean == 185.0
    assert profile.depth_layers["soc"][0].uncertainty_range == {"Q0.05": 140.0, "Q0.95": 230.0}


@pytest.mark.asyncio
async def test_soilgrids_client_mocked_network(mock_soilgrids_json):
    """Test asynchronous get_soil_properties with mocked network call."""
    client = SoilGridsClient()

    with patch.object(client, "get_json", return_value=mock_soilgrids_json) as mock_get:
        profile = await client.get_soil_properties(latitude=28.6139, longitude=77.2090)

        assert mock_get.called
        assert profile.soc_g_kg == 18.5
        assert profile.ph_h2o == 7.2


def test_soilgrids_client_sync_mocked_network(mock_soilgrids_json):
    """Test synchronous get_soil_properties_sync with mocked network call."""
    client = SoilGridsClient()

    with patch.object(client, "get_json_sync", return_value=mock_soilgrids_json) as mock_get:
        profile = client.get_soil_properties_sync(latitude=28.6139, longitude=77.2090)

        assert mock_get.called
        assert profile.cec_cmolc_kg == 21.0
