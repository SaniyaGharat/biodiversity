"""Verification script for New Scenarios: Humid Tropics Deforestation & Temperate Grassland Overgrazing."""

import json
from daaruka.reasoning.models import SiteAssessmentInput
from daaruka.reasoning.engine import MultiMetricReasoningEngine

engine = MultiMetricReasoningEngine()

print("=" * 80)
print("SCENARIO 2: HUMID TROPICS DEFORESTATION & BUFFER DEGRADATION")
print("=" * 80)

trop_site = SiteAssessmentInput(
    soc_pct=2.1,
    ph=4.8,
    moisture_level="humid",
    current_land_use="deforested cattle pasture & fragmented forest buffer",
    rainfall_pattern="tropical monsoon humid",
    annual_precipitation_mm=2100.0,
    management_goals="restore forest buffer, prevent edge erosion, connect wildlife corridor",
    biome="tropical moist broadleaf forest",
)

trop_output = engine.evaluate(trop_site)
print(json.dumps(trop_output.model_dump(), indent=2))

print("\n" + "=" * 80)
print("SCENARIO 3: TEMPERATE GRASSLAND OVERGRAZING & PASTURE DEGRADATION")
print("=" * 80)

grass_site = SiteAssessmentInput(
    soc_pct=1.8,
    ph=6.5,
    moisture_level="moderate",
    current_land_use="intensive continuous cattle grazing",
    rainfall_pattern="temperate continental",
    annual_precipitation_mm=750.0,
    management_goals="alleviate soil compaction, improve forage resilience, sequester carbon",
    biome="temperate grassland steppe",
)

grass_output = engine.evaluate(grass_site)
print(json.dumps(grass_output.model_dump(), indent=2))
