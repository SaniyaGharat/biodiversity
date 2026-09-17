# Sourced Open Datasets Catalog for Biodiversity Intelligence

This document details the curated, citable open datasets selected for the Daaruka.Earth Biodiversity Intelligence Chatbot across 5 core ecological pillars and 1 synthesis/benchmark pillar.

---

## 1. Soil Health

### **SoilGrids250m & FAO Harmonized World Soil Database (HWSD v2.0)**
- **Source / Organization:** ISRIC – World Soil Information & FAO (Food and Agriculture Organization of the United Nations).
- **Domain:** Global digital soil mapping and physical/chemical soil characteristics at 250m spatial resolution.
- **Variables Covered:**
  - `soc`: Soil Organic Carbon stock (t/ha) and concentration (dg/kg)
  - `phh2o`: Soil pH in H2O solution (acidity/alkalinity)
  - `cec`: Cation Exchange Capacity at pH 7 (cmolc/kg) - indicates nutrient holding capacity
  - `sand`, `silt`, `clay`: Mass fraction of particle sizes (%) - determines soil texture class
  - `bdod`: Bulk density of fine earth fraction (cg/cm³)
  - `nitrogen`: Total nitrogen content (cg/kg)
- **Access Method:**
  - **REST API:** ISRIC SoilGrids REST API (`https://rest.isric.org/soilgrids/v2.0/properties/query?lon={lon}&lat={lat}`)
  - **OGC WCS / WFS:** Web Coverage Services for spatial bounding-box querying
  - **Bulk Data:** GeoTIFF raster tiles downloadable via ISRIC WebDAV and FAO HWSD portal
- **Citation:**
  > Poggio, L., de Sousa, L. M., Batjes, N. H., et al. (2021). *SoilGrids 2.0: producing soil information for the globe with quantified spatial uncertainty*. SOIL, 7(1), 217-240.

---

## 2. Biodiversity Indicators

### **GBIF (Global Biodiversity Information Facility) & IUCN Red List**
- **Source / Organization:** GBIF Secretariat & International Union for Conservation of Nature (IUCN).
- **Domain:** Species distribution, occurrence records, taxonomic hierarchy, and conservation status.
- **Variables Covered:**
  - `scientificName`, `vernacularName`: Species taxonomic identification
  - `decimalLatitude`, `decimalLongitude`: Georeferenced occurrence points
  - `iucnRedListCategory`: Threat level (EX, CR, EN, VU, NT, LC)
  - `eventDate`, `year`: Temporal observation records
  - `basisOfRecord`: Observation type (HUMAN_OBSERVATION, PRESERVED_SPECIMEN, MACHINE_OBSERVATION)
  - `taxonomicBackbone`: Kingdom, Phylum, Class, Order, Family, Genus
- **Access Method:**
  - **REST API:** GBIF Occurrence API (`https://api.gbif.org/v1/occurrence/search?decimalLatitude={lat}&decimalLongitude={lon}&radius={r}`)
  - **Species API:** GBIF Species API (`https://api.gbif.org/v1/species/match?name={name}`)
  - **Bulk Export:** Darwin Core Archive (DwC-A) in CSV/Parquet format via GBIF download service
- **Citation:**
  > GBIF.org (2024). *GBIF Occurrence Download*. https://doi.org/10.15468/dl.sample

---

## 3. Land Use & Land Cover (LULC)

### **Copernicus Global Land Cover (CGLS-LC100) / ESA WorldCover 10m**
- **Source / Organization:** European Space Agency (ESA) & Copernicus Land Monitoring Service (CLMS).
- **Domain:** Global high-resolution Earth observation land cover classification and fractional cover maps.
- **Variables Covered:**
  - `Discrete_Classification`: Dominant land cover class (Tree cover, Shrubland, Grassland, Cropland, Built-up, Bare / sparse vegetation, Permanent water bodies, Herbaceous wetland)
  - `Forest_Type`: Evergreen needleleaf, deciduous broadleaf, mixed forest
  - `Fractional_Cover`: Percentage cover per 100m/10m pixel for Trees, Shrubs, Grass, Crops, Urban, Water
  - `Quality_Flags`: Cloud/shadow quality and observation confidence
- **Access Method:**
  - **API:** Copernicus Data Space Ecosystem STAC API (`https://catalogue.dataspace.copernicus.eu/stac`)
  - **Cloud Optimized GeoTIFF (COG):** Direct S3 / HTTP range requests for bounding box tile fetching
  - **Bulk Downloads:** Yearly global composites (2015–2023)
- **Citation:**
  > Buchhorn, M., Smets, B., Bertels, L., et al. (2020). *Copernicus Global Land Service: Land Cover 100m: version 3 Globe 2015-2019: Product User Manual*. Geneve: Zenodo. https://doi.org/10.5281/zenodo.3939050

---

## 4. Climate Factors & Bioclimatic Stress

### **WorldClim v2.1 & ERA5-Land (Copernicus / ECMWF)**
- **Source / Organization:** WorldClim (Fick & Hijmans) & European Centre for Medium-Range Weather Forecasts (ECMWF).
- **Domain:** High-resolution global climate grids and multi-decade atmospheric/terrestrial reanalysis.
- **Variables Covered:**
  - `BIO1`: Annual Mean Temperature (°C)
  - `BIO4`: Temperature Seasonality (Standard Deviation × 100)
  - `BIO5` & `BIO6`: Max Temperature of Warmest Month & Min Temperature of Coldest Month
  - `BIO12`: Annual Precipitation (mm)
  - `BIO15`: Precipitation Seasonality (Coefficient of Variation)
  - `BIO16` & `BIO17`: Precipitation of Wettest & Driest Quarters
  - `srad`, `vapr`, `wind`: Solar radiation (kJ m⁻² day⁻¹), vapor pressure (kPa), wind speed (m s⁻¹)
- **Access Method:**
  - **API:** ECMWF Copernicus Climate Data Store (CDS) API via `cdsapi` Python client
  - **WorldClim Direct Downloads:** 30 arc-seconds (~1km²) GeoTIFF and NetCDF files
- **Citation:**
  > Fick, S. E., & Hijmans, R. J. (2017). *WorldClim 2: new 1-km spatial resolution climate surfaces for global land areas*. International Journal of Climatology, 37(12), 4302-4315.

---

## 5. Human Impact & Anthropogenic Modification

### **Global Human Modification (GHM) & Global Human Footprint (NASA SEDAC)**
- **Source / Organization:** NASA Socioeconomic Data and Applications Center (SEDAC / CIESIN Columbia University) & The Nature Conservancy.
- **Domain:** Quantitative spatial estimation of direct human modification of terrestrial lands.
- **Variables Covered:**
  - `GHM Score`: Continuous scale (0.0 = untouched natural habitat, 1.0 = intensely modified urban/industrial landscape)
  - `Built_Environments`: Settlement structures, impervious surfaces, urban extents
  - `Cropland_Pasture`: Agricultural conversion pressure
  - `Transportation_Corridors`: Distance and density to roads, railways, and navigable waterways
  - `Human_Population_Density`: Gridded Population of the World (GPWv4)
  - `Nighttime_Lights`: Anthropogenic electrical illumination intensity
- **Access Method:**
  - **SEDAC REST API:** NASA SEDAC OGC Web Mapping Service and REST endpoints
  - **GeoTIFF / HDF Downloads:** 1km global resolution rasters from NASA Earthdata
- **Citation:**
  > Theobald, D. M., et al. (2020). *Earth transformed: detailed mapping of global human modification from 1990 to 2017*. Earth System Science Data, 12(3), 1953–1972.

---

## 6. Synthesis, Tipping Points & Benchmarks

### **IPCC Sixth Assessment Report (AR6 WGII) & IPBES Global Assessment**
- **Source / Organization:** Intergovernmental Panel on Climate Change (IPCC) & Intergovernmental Science-Policy Platform on Biodiversity and Ecosystem Services (IPBES).
- **Domain:** Synthesized evidence, ecosystem vulnerability baselines, biodiversity loss thresholds, and regional adaptation metrics.
- **Variables / Metrics Covered:**
  - Regional ecosystem vulnerability indexes
  - Species extinction risk trajectories under 1.5°C vs 2.0°C warming scenarios
  - Nature's Contributions to People (NCP) degradation indicators
  - Ecological resilience and carbon sink preservation thresholds
- **Access Method:**
  - **Reports & Synthesis:** IPCC / IPBES Summary for Policymakers and Chapter Reports (PDF / XML)
  - **IPCC Data Distribution Centre (DDC):** Tabular CSVs and NetCDF regional scenario projections
- **Citation:**
  > IPCC (2022). *Climate Change 2022: Impacts, Adaptation and Vulnerability. Contribution of Working Group II to the Sixth Assessment Report of the Intergovernmental Panel on Climate Change*. Cambridge University Press.
