"""ISRIC SoilGrids REST API v2.0 Client for physical and chemical soil properties."""

import logging
from typing import Dict, List, Optional, Any
from daaruka.knowledge.connectors.base import BaseConnector
from daaruka.knowledge.models import SoilProfile, SoilPropertyLayer

logger = logging.getLogger(__name__)

DEFAULT_SOILGRIDS_PROPERTIES = ["soc", "phh2o", "cec", "clay", "sand", "silt", "bdod", "nitrogen"]
DEFAULT_DEPTHS = ["0-5cm", "5-15cm", "15-30cm", "30-60cm"]


class SoilGridsClient(BaseConnector):
    """Thin client for querying ISRIC SoilGrids 250m v2.0 REST API."""

    def __init__(self, base_url: str = "https://rest.isric.org/soilgrids/v2.0", timeout: float = 15.0):
        super().__init__(base_url=base_url, timeout=timeout)

    def _parse_soilgrids_response(self, raw_data: Dict[str, Any], lat: float, lon: float) -> SoilProfile:
        """Parse raw SoilGrids nested JSON feature into standardized SoilProfile model."""
        properties_data = raw_data.get("properties", {})
        layers = properties_data.get("layers", [])

        layer_map: Dict[str, Dict[str, float]] = {}
        detailed_layers: Dict[str, List[SoilPropertyLayer]] = {}

        for layer in layers:
            prop_name = layer.get("name")
            if not prop_name:
                continue

            depth_list: List[SoilPropertyLayer] = []
            layer_map[prop_name] = {}

            for depth_item in layer.get("depths", []):
                depth_label = depth_item.get("label", "")
                values = depth_item.get("values", {})
                mean_val = values.get("mean")

                uncertainty = {}
                if "Q0.05" in values and values["Q0.05"] is not None:
                    uncertainty["Q0.05"] = float(values["Q0.05"])
                if "Q0.95" in values and values["Q0.95"] is not None:
                    uncertainty["Q0.95"] = float(values["Q0.95"])

                if mean_val is not None:
                    layer_map[prop_name][depth_label] = float(mean_val)
                    depth_list.append(
                        SoilPropertyLayer(
                            depth_interval=depth_label,
                            mean=float(mean_val),
                            uncertainty_range=uncertainty if uncertainty else None,
                        )
                    )

            detailed_layers[prop_name] = depth_list

        # Extract topsoil (0-5cm or 0-30cm average) with standardized unit conversions
        # phh2o: SoilGrids provides pH*10 -> convert to standard pH
        ph_raw = layer_map.get("phh2o", {}).get("0-5cm") or layer_map.get("phh2o", {}).get("5-15cm")
        ph_h2o = round(ph_raw / 10.0, 2) if ph_raw is not None else None

        # soc: SoilGrids provides dg/kg -> convert to g/kg (divide by 10)
        soc_raw = layer_map.get("soc", {}).get("0-5cm") or layer_map.get("soc", {}).get("5-15cm")
        soc_g_kg = round(soc_raw / 10.0, 2) if soc_raw is not None else None

        # Estimated SOC stock in 0-30cm (t/ha) approx if soc and bdod available
        soc_stock_t_ha = None
        if soc_g_kg is not None:
            # Typical conversion proxy: soc(g/kg) * bulk_density(g/cm3) * depth(cm) * 0.1
            bdod_raw = layer_map.get("bdod", {}).get("0-5cm")
            bdod_val = (bdod_raw / 100.0) if bdod_raw is not None else 1.3
            soc_stock_t_ha = round((soc_g_kg / 10.0) * bdod_val * 30 * 1.0, 2)

        # cec: mmol(c)/kg in SoilGrids -> convert to cmol(c)/kg (divide by 10)
        cec_raw = layer_map.get("cec", {}).get("0-5cm")
        cec_cmolc_kg = round(cec_raw / 10.0, 2) if cec_raw is not None else None

        # clay, sand, silt: SoilGrids provides g/kg (0-1000) -> convert to % (0-100%)
        clay_raw = layer_map.get("clay", {}).get("0-5cm")
        clay_pct = round(clay_raw / 10.0, 1) if clay_raw is not None else None

        sand_raw = layer_map.get("sand", {}).get("0-5cm")
        sand_pct = round(sand_raw / 10.0, 1) if sand_raw is not None else None

        silt_raw = layer_map.get("silt", {}).get("0-5cm")
        silt_pct = round(silt_raw / 10.0, 1) if silt_raw is not None else None

        # bdod: cg/cm3 -> g/cm3 (divide by 100)
        bdod_raw = layer_map.get("bdod", {}).get("0-5cm")
        bulk_density = round(bdod_raw / 100.0, 2) if bdod_raw is not None else None

        return SoilProfile(
            latitude=lat,
            longitude=lon,
            soc_g_kg=soc_g_kg,
            soc_stock_t_ha=soc_stock_t_ha,
            ph_h2o=ph_h2o,
            cec_cmolc_kg=cec_cmolc_kg,
            clay_pct=clay_pct,
            sand_pct=sand_pct,
            silt_pct=silt_pct,
            bulk_density_g_cm3=bulk_density,
            depth_layers=detailed_layers,
            data_source="ISRIC SoilGrids 250m v2.0",
        )

    async def get_soil_properties(
        self,
        latitude: float,
        longitude: float,
        properties: Optional[List[str]] = None,
        depths: Optional[List[str]] = None,
    ) -> SoilProfile:
        """Fetch soil properties asynchronously from SoilGrids REST API."""
        props = properties or DEFAULT_SOILGRIDS_PROPERTIES
        depth_list = depths or DEFAULT_DEPTHS

        params: List[tuple] = [
            ("lon", str(longitude)),
            ("lat", str(latitude)),
        ]
        for prop in props:
            params.append(("property", prop))
        for depth in depth_list:
            params.append(("depth", depth))

        # Query endpoint
        raw_response = await self.get_json("properties/query", params=params)
        return self._parse_soilgrids_response(raw_response, lat=latitude, lon=longitude)

    def get_soil_properties_sync(
        self,
        latitude: float,
        longitude: float,
        properties: Optional[List[str]] = None,
        depths: Optional[List[str]] = None,
    ) -> SoilProfile:
        """Fetch soil properties synchronously from SoilGrids REST API."""
        props = properties or DEFAULT_SOILGRIDS_PROPERTIES
        depth_list = depths or DEFAULT_DEPTHS

        params: List[tuple] = [
            ("lon", str(longitude)),
            ("lat", str(latitude)),
        ]
        for prop in props:
            params.append(("property", prop))
        for depth in depth_list:
            params.append(("depth", depth))

        raw_response = self.get_json_sync("properties/query", params=params)
        return self._parse_soilgrids_response(raw_response, lat=latitude, lon=longitude)
