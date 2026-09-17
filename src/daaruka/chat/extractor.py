"""Structured field extractor parsing site assessment variables from unstructured user text."""

import re
import logging
from typing import Optional, Dict, Any

from daaruka.reasoning.models import SiteAssessmentInput

logger = logging.getLogger(__name__)


def extract_site_assessment_from_text(text: str) -> SiteAssessmentInput:
    """Extract structured SiteAssessmentInput fields from natural language text.
    
    Uses deterministic linguistic pattern matching and entity recognition across
    all 5 core ecological pillars (soil, land use, biodiversity, climate, human impact).
    """
    if not text or not text.strip():
        return SiteAssessmentInput()

    extracted_kwargs: Dict[str, Any] = {}
    lower_text = text.lower()

    # 1. Soil Organic Carbon (SOC) Extraction
    # Matches: "0.3%", "0.3% soc", "soil organic carbon is 0.8%", "soc of 1.2 percent", "soc: 0.5"
    soc_match = re.search(
        r"(?:soc|soil\s+organic\s+carbon|organic\s+carbon)\s*(?:is|of|level|stock|:)?\s*([0-9]+(?:\.[0-9]+)?)\s*%",
        lower_text,
    )
    if not soc_match:
        # Fallback: "[0-9.]+% soc" or "[0-9.]+% organic carbon"
        soc_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*%\s*(?:soc|soil\s+organic\s+carbon|organic\s+carbon)", lower_text)
    if not soc_match:
        # Fallback: "soc is 0.8" or "soil organic carbon is 0.8"
        soc_match = re.search(r"(?:soc|soil\s+organic\s+carbon)\s*(?:is|=|:)\s*([0-9]+(?:\.[0-9]+)?)", lower_text)

    if soc_match:
        try:
            val = float(soc_match.group(1))
            if 0.0 <= val <= 100.0:
                extracted_kwargs["soc_pct"] = val
        except ValueError:
            pass

    # 2. Soil pH Extraction
    # Matches: "pH 6.5", "pH is 7.2", "soil ph of 5.8", "pH: 7.0"
    ph_match = re.search(r"(?:soil\s+)?ph\s*(?:is|of|=|:)?\s*([0-9]+(?:\.[0-9]+)?)", lower_text)
    if ph_match:
        try:
            val = float(ph_match.group(1))
            if 0.0 <= val <= 14.0:
                extracted_kwargs["ph"] = val
        except ValueError:
            pass

    # 3. Soil Moisture Extraction
    if re.search(r"\b(very\s+dry|dry\s+soil|low\s+moisture|arid\s+soil|drought-prone\s+soil|water-stressed)\b", lower_text):
        extracted_kwargs["moisture_level"] = "low / water-stressed"
    elif re.search(r"\b(waterlogged|saturated|high\s+moisture|wet\s+soil|marshy)\b", lower_text):
        extracted_kwargs["moisture_level"] = "saturated / high moisture"
    elif re.search(r"\b(moderate\s+moisture|adequate\s+moisture)\b", lower_text):
        extracted_kwargs["moisture_level"] = "moderate moisture"

    # 4. Land Use & Crop Extraction
    crops = ["wheat", "corn", "maize", "soybean", "rice", "cotton", "barley", "canola", "sunflower", "coffee", "orchard", "vineyard", "pasture", "grassland"]
    found_crops = [c for c in crops if re.search(rf"\b{c}\b", lower_text)]
    
    if re.search(r"\b(monoculture\s+wheat|wheat\s+monoculture|monoculture)\b", lower_text):
        crop_str = f"monoculture {found_crops[0]}" if found_crops else "monoculture cropping"
        extracted_kwargs["current_land_use"] = f"cropland / {crop_str}"
        extracted_kwargs["cropping_pattern"] = "continuous monoculture"
    elif re.search(r"\b(cropland|agriculture|farming|crop\s+field|arable\s+land)\b", lower_text):
        crop_str = f"cultivation of {', '.join(found_crops)}" if found_crops else "arable agriculture"
        extracted_kwargs["current_land_use"] = f"cropland / {crop_str}"
    elif re.search(r"\b(pasture|grazing|rangeland|grassland)\b", lower_text):
        extracted_kwargs["current_land_use"] = "pasture / grassland"
    elif re.search(r"\b(agroforestry|silvopasture)\b", lower_text):
        extracted_kwargs["current_land_use"] = "agroforestry system"
    elif found_crops:
        extracted_kwargs["current_land_use"] = f"cropland / {', '.join(found_crops)} cultivation"

    # 5. Biodiversity / Biome Extraction
    if re.search(r"\b(semi-arid|semiarid|semi\s+arid)\b", lower_text):
        extracted_kwargs["biome"] = "semi-arid"
    elif re.search(r"\b(arid|desert)\b", lower_text):
        extracted_kwargs["biome"] = "arid"
    elif re.search(r"\b(temperate\s+grassland|steppe|prairie)\b", lower_text):
        extracted_kwargs["biome"] = "temperate grassland"
    elif re.search(r"\b(tropical\s+rainforest|tropical\s+moist|tropical)\b", lower_text):
        extracted_kwargs["biome"] = "tropical moist forest"
    elif re.search(r"\b(mediterranean)\b", lower_text):
        extracted_kwargs["biome"] = "mediterranean"
    elif re.search(r"\b(boreal|taiga)\b", lower_text):
        extracted_kwargs["biome"] = "boreal"
    elif re.search(r"\b(biodiversity\s+is\s+declining|loss\s+of\s+biodiversity|declining\s+biodiversity|degraded\s+ecosystem|declining\s+species)\b", lower_text):
        # Infer degraded ecosystem in agricultural biome if not specified
        extracted_kwargs["biome"] = "agricultural landscape / degraded agroecosystem"

    # 6. Climate & Precipitation Extraction
    if re.search(r"\b(?:rainfall|precipitation)\s+(?:is\s+)?(?:low|erratic|irregular|scarce|limited)\b", lower_text) or \
       re.search(r"\b(?:low|erratic|irregular|scarce|limited)\s+(?:and\s+[a-z]+\s+)?(?:rainfall|precipitation)\b", lower_text) or \
       re.search(r"\b(?:drought|seasonal\s+drought|dry\s+summers|arid\s+climate)\b", lower_text):
        extracted_kwargs["rainfall_pattern"] = "low / erratic rainfall with seasonal dry spells"
    elif re.search(r"\b(?:rainfall|precipitation)\s+(?:is\s+)?(?:high|heavy|abundant)\b", lower_text) or \
         re.search(r"\b(?:high|heavy|abundant)\s+(?:annual\s+)?(?:rainfall|precipitation)\b", lower_text):
        extracted_kwargs["rainfall_pattern"] = "high annual rainfall"
    elif re.search(r"\b(?:moderate|temperate)\s+(?:rainfall|precipitation)\b", lower_text):
        extracted_kwargs["rainfall_pattern"] = "moderate, well-distributed rainfall"

    # Temperature
    if re.search(r"\b(hot\s+summers|high\s+temperatures|extreme\s+heat)\b", lower_text):
        extracted_kwargs["temperature_regime"] = "hot summers with high evapotranspiration"
    elif re.search(r"\b(cold\s+winters|frost-prone)\b", lower_text):
        extracted_kwargs["temperature_regime"] = "cold winters with seasonal freezing"

    # 7. Human Impact / Management Practices Extraction
    if re.search(r"\b(conventional\s+tillage|intensive\s+plowing|plowing|inversion\s+tillage|moldboard\s+plow)\b", lower_text):
        extracted_kwargs["tillage_practice"] = "intensive conventional inversion tillage"
    elif re.search(r"\b(no-till|zero-tillage|zero\s+till|conservation\s+tillage|reduced\s+tillage)\b", lower_text):
        extracted_kwargs["tillage_practice"] = "conservation no-till management"
    elif re.search(r"\b(heavy\s+chemical|synthetic\s+fertilizer|pesticides|herbicides)\b", lower_text):
        extracted_kwargs["chemical_inputs"] = "high synthetic chemical input regime"

    # 9. Geographic Coordinates Extraction
    geo_match = re.search(
        r"(?:lat(?:itude)?\s*[:=]?\s*([+-]?[0-9]+(?:\.[0-9]+)?)\s*[,;]\s*lon(?:gitude)?\s*[:=]?\s*([+-]?[0-9]+(?:\.[0-9]+)?))",
        lower_text,
    )
    if not geo_match:
        geo_match = re.search(r"\b([+-]?[0-9]{1,2}\.[0-9]{2,6})\s*,\s*([+-]?[0-9]{1,3}\.[0-9]{2,6})\b", text)

    if geo_match:
        try:
            lat = float(geo_match.group(1))
            lon = float(geo_match.group(2))
            if -90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0:
                extracted_kwargs["latitude"] = lat
                extracted_kwargs["longitude"] = lon
        except ValueError:
            pass

    return SiteAssessmentInput(**extracted_kwargs)
