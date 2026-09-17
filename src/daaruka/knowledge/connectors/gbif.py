"""GBIF (Global Biodiversity Information Facility) Occurrence API Client."""

import math
import logging
from collections import Counter
from typing import Dict, List, Optional, Any, Set
from daaruka.knowledge.connectors.base import BaseConnector
from daaruka.knowledge.models import BiodiversityMetrics, ThreatenedSpeciesRecord

logger = logging.getLogger(__name__)

THREATENED_CATEGORIES: Set[str] = {"CR", "EN", "VU", "NT"}


class GBIFClient(BaseConnector):
    """Thin client for querying GBIF Occurrence API to compute biodiversity indicators."""

    def __init__(self, base_url: str = "https://api.gbif.org/v1/occurrence", timeout: float = 15.0):
        super().__init__(base_url=base_url, timeout=timeout)

    def _calculate_bounding_box(self, lat: float, lon: float, radius_km: float) -> Dict[str, str]:
        """Convert a center coordinate and radius in km to approx latitude/longitude bounding box."""
        # 1 deg latitude ~ 111 km
        lat_delta = radius_km / 111.0
        # 1 deg longitude ~ 111 * cos(lat) km
        lon_delta = radius_km / (111.0 * max(0.01, math.cos(math.radians(lat))))

        min_lat = max(-90.0, lat - lat_delta)
        max_lat = min(90.0, lat + lat_delta)
        min_lon = max(-180.0, lon - lon_delta)
        max_lon = min(180.0, lon + lon_delta)

        return {
            "decimalLatitude": f"{min_lat:.4f},{max_lat:.4f}",
            "decimalLongitude": f"{min_lon:.4f},{max_lon:.4f}",
        }

    def _parse_gbif_response(
        self, raw_data: Dict[str, Any], lat: float, lon: float, radius_km: float
    ) -> BiodiversityMetrics:
        """Process occurrence records into biodiversity proxy indicators."""
        results = raw_data.get("results", [])
        total_count = raw_data.get("count", len(results))

        unique_species: Set[str] = set()
        kingdom_counter: Counter = Counter()
        species_counter: Counter = Counter()
        threatened_map: Dict[str, ThreatenedSpeciesRecord] = {}

        for rec in results:
            # Use species name or scientificName
            sci_name = rec.get("species") or rec.get("scientificName")
            if not sci_name:
                continue

            unique_species.add(sci_name)
            species_counter[sci_name] += 1

            kingdom = rec.get("kingdom", "Unknown")
            if kingdom:
                kingdom_counter[kingdom] += 1

            iucn_cat = rec.get("iucnRedListCategory")
            if iucn_cat and iucn_cat.upper() in THREATENED_CATEGORIES:
                cat_upper = iucn_cat.upper()
                if sci_name not in threatened_map:
                    threatened_map[sci_name] = ThreatenedSpeciesRecord(
                        scientific_name=sci_name,
                        vernacular_name=rec.get("vernacularName"),
                        iucn_category=cat_upper,
                        kingdom=rec.get("kingdom"),
                        family=rec.get("family"),
                        observation_count=1,
                    )
                else:
                    threatened_map[sci_name].observation_count += 1

        top_species = [name for name, _ in species_counter.most_common(5)]
        threatened_list = list(threatened_map.values())

        return BiodiversityMetrics(
            latitude=lat,
            longitude=lon,
            search_radius_km=radius_km,
            species_richness_proxy=len(unique_species),
            total_occurrences_sampled=len(results),
            taxonomic_distribution=dict(kingdom_counter),
            threatened_species_count=len(threatened_list),
            threatened_species=threatened_list,
            top_observed_species=top_species,
            data_source="Global Biodiversity Information Facility (GBIF)",
        )

    async def get_species_metrics(
        self, latitude: float, longitude: float, radius_km: float = 10.0, limit: int = 150
    ) -> BiodiversityMetrics:
        """Query GBIF Occurrence API asynchronously and calculate species richness indicators."""
        bbox = self._calculate_bounding_box(lat=latitude, lon=longitude, radius_km=radius_km)
        params: Dict[str, Any] = {
            "decimalLatitude": bbox["decimalLatitude"],
            "decimalLongitude": bbox["decimalLongitude"],
            "hasCoordinate": "true",
            "hasGeospatialIssue": "false",
            "limit": limit,
        }

        raw_response = await self.get_json("search", params=params)
        return self._parse_gbif_response(raw_response, lat=latitude, lon=longitude, radius_km=radius_km)

    def get_species_metrics_sync(
        self, latitude: float, longitude: float, radius_km: float = 10.0, limit: int = 150
    ) -> BiodiversityMetrics:
        """Query GBIF Occurrence API synchronously and calculate species richness indicators."""
        bbox = self._calculate_bounding_box(lat=latitude, lon=longitude, radius_km=radius_km)
        params: Dict[str, Any] = {
            "decimalLatitude": bbox["decimalLatitude"],
            "decimalLongitude": bbox["decimalLongitude"],
            "hasCoordinate": "true",
            "hasGeospatialIssue": "false",
            "limit": limit,
        }

        raw_response = self.get_json_sync("search", params=params)
        return self._parse_gbif_response(raw_response, lat=latitude, lon=longitude, radius_km=radius_km)
