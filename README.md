# 🌿 Daaruka.Earth: Biodiversity Intelligence Platform

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)](https://fastapi.tiangolo.com/)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-VectorStore-purple.svg)](https://www.trychroma.com/)
[![Tests](https://img.shields.io/badge/tests-34%2F34%20passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/license-MIT-orange.svg)]()

An AI-powered Biodiversity & Ecological Intelligence platform built for the **Darukaa.Earth Hackathon**. The platform synthesizes multi-dimensional ecological datasets (soil health, species occurrence, land use, climate risk, and human disturbance) through a strictly grounded multi-metric reasoning engine, a conversational intelligence layer with multi-turn memory, and automated geospatial data connectors (ISRIC SoilGrids & GBIF).

---

## 🏛️ System Architecture

The platform is designed around four decoupled, modular subsystems:

```
                                ┌────────────────────────────────────────┐
                                │           Client / Consumer            │
                                │    (Web UI, Chat Client, REST API)     │
                                └───────────────────┬────────────────────┘
                                                    │
                                                    ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FastAPI Application                                  │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              API Layer (`api/v1/`)                             │   │
│   │   - `GET  /health` & `GET /api/v1/health`                                      │   │
│   │   - `GET  /api/v1/knowledge/search` (Grounded semantic & topic retrieval)      │   │
│   │   - `POST /api/v1/chat` (Conversational multi-turn slot filling & reasoning)   │   │
│   │   - `POST /api/v1/assess` (Structured JSON input & geo-enrichment evaluation)  │   │
│   └───────────────────────┬────────────────────────────────┬───────────────────────┘   │
│                           │                                │                           │
│                           ▼                                ▼                           │
│   ┌───────────────────────────────────┐    ┌───────────────────────────────────────┐   │
│   │        Chat Layer (`chat/`)       │    │     Reasoning Engine (`reasoning/`)   │   │
│   │  - Multi-turn session memory      │    │  - Gap Detection (5-variable analysis)│   │
│   │  - Slot-filling NLP extraction    │◄───┤  - Multi-variable interaction rules   │   │
│   │  - Non-repeating clarifying Qs    │    │  - Numeric grounding claim validator  │   │
│   │  - Human-readable text formatting │    │  - Calibrated confidence scoring      │   │
│   └─────────────────┬─────────────────┘    └───────────────────┬───────────────────┘   │
│                     │                                          │                       │
│                     ▼                                          ▼                       │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           Knowledge Layer (`knowledge/`)                       │   │
│   │   - Document Ingestion & Page-boundary tracking (`ingest.py`, `chunker.py`)     │   │
│   │   - Vector Store (`vector_store.py` backed by ChromaDB)                        │   │
│   │   - Semantic + Topic-Filtered Retriever (`retriever.py`)                       │   │
│   │   - Geospatial Connectors: SoilGrids (ISRIC REST) & GBIF (Occurrence REST)     │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

### Module Breakdown
- **API Layer (`src/daaruka/api/v1/`)**: FastAPI routing, validation, error handling, and response serialization supporting both JSON and human-readable Markdown/text formats.
- **Knowledge Layer (`src/daaruka/knowledge/`)**: PDF parsing (`pypdf`), chunking with exact document title and page number attribution, ChromaDB vector indexing, and REST connectors for SoilGrids (pH, SOC, moisture) and GBIF (species richness proxy).
- **Reasoning Engine (`src/daaruka/reasoning/`)**:
  - `gap_detector.py`: Evaluates data completeness across the 5 core variables (soil, land use, climate, region/biome, coordinates).
  - `rules.py`: Synthesizes multi-variable ecological trade-offs (e.g., SOC deficit × semi-arid climate × tillage disruption).
  - `validator.py`: Enforces strict grounding — verifying chunk IDs exist and preventing numeric hallucinations by matching quantitative claims against retrieved source text.
- **Chat Layer (`src/daaruka/chat/`)**: Conversational loop maintaining session state, accumulating user-provided site parameters, generating context-aware clarifying questions, and formatting evidence-backed reports.

---

## 🗄️ Database & Schema

### 1. Vector Store: ChromaDB
- **Storage Location**: `./chroma_data/`
- **Collection Name**: `biodiversity_knowledge`
- **Total Chunks**: **4,472 indexed chunks**
- **Embedding Model**: Default ONNX MiniLM-L6-v2 (`all-MiniLM-L6-v2`) via `chromadb.utils.embedding_functions.DefaultEmbeddingFunction`.
- **Corpus Ingested**:
  1. **FAO Recarbonizing Global Soils (Vol 3: Cropland & Grassland Systems)**: 4,000+ chunks covering soil organic carbon sequestration, agroforestry, conservation tillage, and nutrient management.
  2. **IPCC AR6 WGII Chapter 2 (Terrestrial & Freshwater Ecosystems)**: 400+ chunks covering biodiversity tipping points, climate velocity, and ecosystem resilience.
  3. **CBD COP15 Decision 15/4 (Kunming-Montreal Global Biodiversity Framework)**: Chunks covering 2030 restoration targets and conservation policy.
- **Chunk Metadata Schema**:
  ```json
  {
    "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3)",
    "page_number": 21,
    "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
    "year": 2021,
    "topics": "soil,carbon,cover-cropping,agriculture,soc,tillage",
    "url_or_doi": "https://doi.org/10.4060/cb6595en"
  }
  ```

### 2. Session Store: In-Memory State
- **Storage Model**: Python in-memory dictionary keyed by `session_id` (`src/daaruka/chat/session.py`).
- **Session Data Structure**:
  - `session_id`: Unique string identifier.
  - `assessment_input`: Accumulated `SiteAssessmentInput` fields across turns.
  - `history`: Full conversation turn history.
  - `clarified_fields`: Set of variables already queried to avoid repetitive clarifying questions.
- > [!NOTE]
  > **Hackathon-Scope Limitation**: The session store is non-persistent across server restarts. In a full production deployment, this would be backed by Redis or PostgreSQL.

---

## 🚀 Local Setup & Installation

Follow these exact steps from `git clone` to a running server.

### 1. Clone the Repository
```bash
git clone https://github.com/SaniyaGharat/biodiversity.git
cd biodiversity
```

### 2. Create and Activate Virtual Environment
```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate

# Windows (PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy the environment template:
```bash
cp .env.example .env
```
Default settings run completely locally without requiring external API keys.

### 5. (Optional) Run Corpus Ingestion
The repository includes the pre-indexed ChromaDB database in `./chroma_data/`. To re-download the source PDFs and re-index the corpus from scratch:
```bash
python -m daaruka.knowledge.download_real_corpus
python -m daaruka.knowledge.ingest
```

### 6. Start the FastAPI Server
```bash
uvicorn daaruka.main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger UI)**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc UI**: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check**: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Testing & CI/CD

> [!NOTE]
> **CI/CD Pipeline**: No CI/CD pipeline configured — pytest run manually; see `tests/` for the 34-test suite.

Run the entire 34-test automated test suite:
```bash
pytest
```

Test coverage includes:
- **`tests/test_audit_scenarios.py`**: Multi-biome validation across Semi-arid Cropland, Humid Tropics Deforestation, and Temperate Grasslands.
- **`tests/test_assess.py`**: Structured JSON assessment and SoilGrids/GBIF geo-enrichment.
- **`tests/test_chat.py`**: Multi-turn dialog, slot extraction, memory persistence, and clarifying questions.
- **`tests/test_reasoning.py`**: Gap detection, multi-variable interactions, and numeric-grounding validator.
- **`tests/test_knowledge_retrieval.py`**: Semantic search, page citations, and chunking.
- **`tests/test_soilgrids_connector.py` & `test_gbif_connector.py`**: Live and mocked geospatial connectors.
- **`tests/test_health.py`**: Sync/async healthcheck endpoints.

---

## 📖 API Reference

### 1. Health Check
`GET /health` or `GET /api/v1/health`

**Example Request**:
```bash
curl -X GET http://localhost:8000/health
```

**Actual Live Response (`200 OK`)**:
```json
{
  "status": "healthy",
  "service": "daaruka-backend",
  "version": "0.1.0",
  "timestamp": "2026-09-17T17:23:14.308907+00:00",
  "environment": "production"
}
```

---

### 2. Semantic Knowledge Search
`GET /api/v1/knowledge/search`

Search the grounded knowledge base with optional topic tags filtering (`soil`, `carbon`, `restoration`, `policy`, `climate`).

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/knowledge/search?query=soil+organic+carbon+cover+cropping&top_k=1&tags=soil"
```

**Actual Live Response (`200 OK`)**:
```json
{
  "query": "soil organic carbon cover cropping",
  "total_results": 1,
  "results": [
    {
      "chunk_id": "4d894bde-2aef-5c18-9038-33512302261e",
      "content": "VOLUME 3: CROPLAND, GRASSLAND, INTEGRATED SYSTEMS AND FARMING APPROACHES  PRACTICES OVERVIEW 3 \n2. Range of applicability Cover cropping (CC) can be applied worldwide, but there is not a cover crop that fits every farming situation and potential benefits vary with climate, soil type and plant species. In detail, CCs can better fit in humid and subhumid regions than in semiarid regions where precipitation is limited (Unger and Vigil, 1998). The possible competition of CCs for available soil water in semiarid regions can limit the adoption of the practice (Unger and Vigil, 1998; Nielsen et al., 2015). A different approach to agricultural management is required for arable and woody crops.  \n3. Impact on soil organic carbon stocks The C storage",
      "similarity_score": 0.7241,
      "citation": {
        "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)",
        "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
        "year": 2021,
        "section_title": "Page 21",
        "page": 21,
        "topics": [
          "soil",
          "carbon",
          "cover-cropping",
          "agriculture",
          "soc",
          "tillage",
          "soil-organic-carbon"
        ],
        "url_or_doi": "https://doi.org/10.4060/cb6595en"
      }
    }
  ]
}
```

---

### 3. Multi-Turn Conversational Chat
`POST /api/v1/chat`

Handles free-text input, extracts ecological parameters, maintains multi-turn session state, asks non-repeating clarifying questions for missing data, and generates grounded recommendations.

#### Turn 1: Partial Input (Triggers Non-Repeating Clarifying Question)
**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "demo_turn1",
    "message": "I have a 20-hectare wheat farm in semi-arid Spain with 0.8% soil organic carbon."
  }'
```

**Actual Live Response (`200 OK`)**:
```json
{
  "session_id": "demo_turn1",
  "response_text": "What is the typical climate and precipitation pattern on your land (e.g. semi-arid with low/erratic rainfall, seasonal drought, or temperature extremes)?",
  "session_state_summary": {
    "session_id": "demo_turn1",
    "accumulated_fields": {
      "soc_pct": 0.8,
      "current_land_use": "cropland / arable agriculture",
      "biome": "semi-arid"
    },
    "data_completeness_score": 0.6,
    "missing_categories": [
      "climate",
      "human_impact"
    ],
    "present_categories": [
      "soil",
      "land_use",
      "biodiversity"
    ],
    "total_messages": 1
  },
  "is_asking_clarification": true,
  "recommendations": null,
  "extracted_in_this_turn": {
    "soc_pct": 0.8,
    "current_land_use": "cropland / arable agriculture",
    "biome": "semi-arid"
  }
}
```

#### Turn 2: Grounded Recommendation Generation
**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "readme_demo_session",
    "message": "I manage 50 hectares of cropland in a semi-arid zone with sandy soil and 0.8% organic carbon."
  }'
```

**Actual Live Response (`200 OK`)**:
```json
{
  "session_id": "readme_demo_session",
  "response_text": "Based on the multi-variable ecological profile of your site, here are targeted, scientifically grounded recommendations:\n\n**Overall Assessment Confidence**: `HIGH`\n*Overall assessment confidence is rated HIGH based on 3 peer-reviewed action(s) with verified page-level citations from FAO/IPCC/CBD literature and 2 missing ecological pillar(s).*\n\n### 1. Integrate Multi-Species Agroforestry Hedgerows & Field Margins\n**Ecological Mechanism**: Combining woody perennials with annual crops establishes structural diversity that buffers microclimates against heat extremes, reduces wind-driven evapotranspiration, and creates continuous ecological corridors for beneficial pollinator and predator taxa across monoculture landscapes.\n\n**Cross-Variable Interactions & Synergies**:\n- *Vegetation Structural Diversity <-> Microclimate Thermal Buffering*\n- *Landscape Heterogeneity <-> Pollinator & Predator Abundance*\n- *Tree Root Biomass <-> Deep Soil Carbon Stabilization*\n\n**Impacted Metrics**: Field Evaporative Water Loss, Soil Organic Carbon in subsoil layers, Species Richness Proxy & Pollinator Density, Ecological Connectivity (CBD Target 10)\n**Expected Outcome**: Increases carbon storage through combined aboveground and belowground tree biomass, enhances structural landscape heterogeneity, and advances biodiversity-friendly management.\n**Implementation Horizon**: `medium-term` | **Scientific Confidence**: `HIGH`\n\n**Scientific Evidence & Citations**:\n- [Food and Agriculture Organization of the United Nations (FAO), 2021] *Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)* (p. 590) (https://doi.org/10.4060/cb6595en)\n- [Convention on Biological Diversity (CBD / UNEP), 2022] *CBD COP15 Decision 15/4: Kunming-Montreal Global Biodiversity Framework* (p. 4) (https://www.cbd.int/doc/decisions/cop-15/cop-15-dec-04-en.pdf)\n\n### 2. Implement Seasonal Legume Cover Cropping Tailored to Semiarid Moisture Constraints\n**Ecological Mechanism**: Introducing drought-adapted leguminous cover crops fixes atmospheric nitrogen to enhance microbial C:N balance and build topsoil organic carbon. In semiarid regions where precipitation is limited, careful selection of cover crop species and growth windows avoids soil water competition with primary crops (Unger and Vigil, 1998).\n\n**Cross-Variable Interactions & Synergies**:\n- *Legume Nitrogen Fixation <-> Soil Microbial Carbon Stabilization*\n- *Cover Crop Water Demand <-> Semiarid Available Soil Moisture*\n- *Crop Diversification <-> Soil Biota Redundancy*\n\n**Impacted Metrics**: Topsoil Organic Carbon Stock (SOC), Available Soil Moisture Retention, Soil Microbial Parameters\n**Expected Outcome**: Enhances soil organic carbon stocks while managing potential soil water competition in semiarid environments, improving water infiltration and aggregate stability.\n**Implementation Horizon**: `short-term` | **Scientific Confidence**: `HIGH`\n\n**Scientific Evidence & Citations**:\n- [Food and Agriculture Organization of the United Nations (FAO), 2021] *Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)* (p. 21) (https://doi.org/10.4060/cb6595en)\n\n### 3. Transition to Conservation Tillage & Residue Retention Management\n**Ecological Mechanism**: Eliminating or reducing intensive tillage avoids continuous soil aggregate disruption in topsoil layers, reducing oxidative carbon losses while increasing water infiltration and reducing soil erosion.\n\n**Cross-Variable Interactions & Synergies**:\n- *Tillage Reduction <-> Soil Organic Carbon Accumulation*\n- *Soil Structure Protection <-> Infiltration Capacity*\n\n**Impacted Metrics**: Topsoil Organic Carbon Retention, Soil Macroaggregate Stability, Surface Evaporative Water Loss\n**Expected Outcome**: Stabilizes topsoil organic carbon and improves soil structure retention compared to conventional inversion plowing.\n**Implementation Horizon**: `short-term` | **Scientific Confidence**: `HIGH`\n\n**Scientific Evidence & Citations**:\n- [Food and Agriculture Organization of the United Nations (FAO), 2021] *Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)* (p. 590) (https://doi.org/10.4060/cb6595en)\n\n---\n*These recommendations are grounded in peer-reviewed protocols from FAO, IPCC AR6 WGII, and the CBD Kunming-Montreal Framework.*",
  "session_state_summary": {
    "session_id": "readme_demo_session",
    "accumulated_fields": {
      "soc_pct": 0.8,
      "current_land_use": "cropland / arable agriculture",
      "biome": "semi-arid"
    },
    "data_completeness_score": 0.6,
    "missing_categories": [
      "climate",
      "human_impact"
    ],
    "present_categories": [
      "soil",
      "land_use",
      "biodiversity"
    ],
    "total_messages": 1
  },
  "is_asking_clarification": false,
  "recommendations": [
    {
      "action": "Integrate Multi-Species Agroforestry Hedgerows & Field Margins",
      "mechanism": "Combining woody perennials with annual crops establishes structural diversity that buffers microclimates against heat extremes, reduces wind-driven evapotranspiration, and creates continuous ecological corridors for beneficial pollinator and predator taxa across monoculture landscapes.",
      "variable_interactions": [
        "Vegetation Structural Diversity <-> Microclimate Thermal Buffering",
        "Landscape Heterogeneity <-> Pollinator & Predator Abundance",
        "Tree Root Biomass <-> Deep Soil Carbon Stabilization"
      ],
      "impacted_metrics": [
        "Field Evaporative Water Loss",
        "Soil Organic Carbon in subsoil layers",
        "Species Richness Proxy & Pollinator Density",
        "Ecological Connectivity (CBD Target 10)"
      ],
      "estimated_effect": "Increases carbon storage through combined aboveground and belowground tree biomass, enhances structural landscape heterogeneity, and advances biodiversity-friendly management.",
      "time_horizon": "medium-term",
      "confidence": "high",
      "sources": [
        {
          "chunk_id": "3721df08-2bb9-5fe4-ba72-84120b145bd8",
          "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)",
          "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
          "year": 2021,
          "section_title": "Page 590",
          "page": 590,
          "url_or_doi": "https://doi.org/10.4060/cb6595en",
          "citation": "[Food and Agriculture Organization of the United Nations (FAO), 2021] Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems) (p. 590) [https://doi.org/10.4060/cb6595en]"
        },
        {
          "chunk_id": "09afa2f6-2e2a-5d0a-9b38-9b45b3cd0794",
          "document_title": "CBD COP15 Decision 15/4: Kunming-Montreal Global Biodiversity Framework",
          "publisher": "Convention on Biological Diversity (CBD / UNEP)",
          "year": 2022,
          "section_title": "Page 4",
          "page": 4,
          "url_or_doi": "https://www.cbd.int/doc/decisions/cop-15/cop-15-dec-04-en.pdf",
          "citation": "[Convention on Biological Diversity (CBD / UNEP), 2022] CBD COP15 Decision 15/4: Kunming-Montreal Global Biodiversity Framework (p. 4) [https://www.cbd.int/doc/decisions/cop-15/cop-15-dec-04-en.pdf]"
        }
      ]
    },
    {
      "action": "Implement Seasonal Legume Cover Cropping Tailored to Semiarid Moisture Constraints",
      "mechanism": "Introducing drought-adapted leguminous cover crops fixes atmospheric nitrogen to enhance microbial C:N balance and build topsoil organic carbon. In semiarid regions where precipitation is limited, careful selection of cover crop species and growth windows avoids soil water competition with primary crops (Unger and Vigil, 1998).",
      "variable_interactions": [
        "Legume Nitrogen Fixation <-> Soil Microbial Carbon Stabilization",
        "Cover Crop Water Demand <-> Semiarid Available Soil Moisture",
        "Crop Diversification <-> Soil Biota Redundancy"
      ],
      "impacted_metrics": [
        "Topsoil Organic Carbon Stock (SOC)",
        "Available Soil Moisture Retention",
        "Soil Microbial Parameters"
      ],
      "estimated_effect": "Enhances soil organic carbon stocks while managing potential soil water competition in semiarid environments, improving water infiltration and aggregate stability.",
      "time_horizon": "short-term",
      "confidence": "high",
      "sources": [
        {
          "chunk_id": "4d894bde-2aef-5c18-9038-33512302261e",
          "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)",
          "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
          "year": 2021,
          "section_title": "Page 21",
          "page": 21,
          "url_or_doi": "https://doi.org/10.4060/cb6595en",
          "citation": "[Food and Agriculture Organization of the United Nations (FAO), 2021] Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems) (p. 21) [https://doi.org/10.4060/cb6595en]"
        }
      ]
    },
    {
      "action": "Transition to Conservation Tillage & Residue Retention Management",
      "mechanism": "Eliminating or reducing intensive tillage avoids continuous soil aggregate disruption in topsoil layers, reducing oxidative carbon losses while increasing water infiltration and reducing soil erosion.",
      "variable_interactions": [
        "Tillage Reduction <-> Soil Organic Carbon Accumulation",
        "Soil Structure Protection <-> Infiltration Capacity"
      ],
      "impacted_metrics": [
        "Topsoil Organic Carbon Retention",
        "Soil Macroaggregate Stability",
        "Surface Evaporative Water Loss"
      ],
      "estimated_effect": "Stabilizes topsoil organic carbon and improves soil structure retention compared to conventional inversion plowing.",
      "time_horizon": "short-term",
      "confidence": "high",
      "sources": [
        {
          "chunk_id": "3721df08-2bb9-5fe4-ba72-84120b145bd8",
          "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)",
          "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
          "year": 2021,
          "section_title": "Page 590",
          "page": 590,
          "url_or_doi": "https://doi.org/10.4060/cb6595en",
          "citation": "[Food and Agriculture Organization of the United Nations (FAO), 2021] Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems) (p. 590) [https://doi.org/10.4060/cb6595en]"
        }
      ]
    }
  ],
  "extracted_in_this_turn": {
    "soc_pct": 0.8,
    "current_land_use": "cropland / arable agriculture",
    "biome": "semi-arid"
  }
}
```

---

### 4. Structured Assessment & Geo-Enrichment
`POST /api/v1/assess`

Programmatic evaluation endpoint accepting structured `SiteAssessmentInput` JSON. Automatically queries **SoilGrids** and **GBIF** when coordinates (`latitude`, `longitude`) are provided. Supports `?format=json` (default) and `?format=text`.

#### JSON Format:
**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/assess?format=json" \
  -H "Content-Type: application/json" \
  -d '{
    "land_use": "cropland",
    "soc_percent": 0.8,
    "rainfall_mm": 350.0,
    "region": "semi-arid"
  }'
```

**Actual Live Response (`200 OK`)**:
```json
{
  "site_summary": {
    "region": "semi-arid"
  },
  "gap_analysis": {
    "missing_categories": [
      "soil",
      "land_use",
      "climate",
      "human_impact"
    ],
    "present_categories": [
      "biodiversity"
    ],
    "data_completeness_score": 0.2,
    "suggested_clarifications": [
      "What is your current topsoil organic carbon (SOC%), soil pH, or baseline moisture level?",
      "What is the current land use or cropping system (e.g. continuous monoculture, crop rotation, pasture)?",
      "What are your typical annual precipitation and temperature patterns (e.g. semi-arid with <400mm rainfall, seasonal drought)?",
      "What current land management practices are applied (e.g. intensive moldboard plowing vs no-till, synthetic inputs vs organic)?"
    ]
  },
  "enriched_geo_data": null,
  "data_provenance": {
    "region": "user-provided"
  },
  "overall_confidence": "medium",
  "confidence_rationale": "Overall assessment confidence is rated MEDIUM based on 2 peer-reviewed action(s) with verified page-level citations from FAO/IPCC/CBD literature and 4 missing ecological pillar(s).",
  "retrieved_evidence_count": 8,
  "cross_variable_insights": [],
  "recommendations": [
    {
      "action": "Integrate Multi-Species Agroforestry Hedgerows & Field Margins",
      "mechanism": "Combining woody perennials with annual crops establishes structural diversity that buffers microclimates against heat extremes, reduces wind-driven evapotranspiration, and creates continuous ecological corridors for beneficial pollinator and predator taxa across monoculture landscapes.",
      "variable_interactions": [
        "Vegetation Structural Diversity <-> Microclimate Thermal Buffering",
        "Landscape Heterogeneity <-> Pollinator & Predator Abundance",
        "Tree Root Biomass <-> Deep Soil Carbon Stabilization"
      ],
      "impacted_metrics": [
        "Field Evaporative Water Loss",
        "Soil Organic Carbon in subsoil layers",
        "Species Richness Proxy & Pollinator Density",
        "Ecological Connectivity (CBD Target 10)"
      ],
      "estimated_effect": "Increases carbon storage through combined aboveground and belowground tree biomass, enhances structural landscape heterogeneity, and advances biodiversity-friendly management.",
      "time_horizon": "medium-term",
      "confidence": "high",
      "sources": [
        {
          "chunk_id": "09afa2f6-2e2a-5d0a-9b38-9b45b3cd0794",
          "document_title": "CBD COP15 Decision 15/4: Kunming-Montreal Global Biodiversity Framework",
          "publisher": "Convention on Biological Diversity (CBD / UNEP)",
          "year": 2022,
          "section_title": "Page 4",
          "page": 4,
          "url_or_doi": "https://www.cbd.int/doc/decisions/cop-15/cop-15-dec-04-en.pdf",
          "citation": "[Convention on Biological Diversity (CBD / UNEP), 2022] CBD COP15 Decision 15/4: Kunming-Montreal Global Biodiversity Framework (p. 4) [https://www.cbd.int/doc/decisions/cop-15/cop-15-dec-04-en.pdf]"
        }
      ]
    },
    {
      "action": "Implement Seasonal Legume Cover Cropping Tailored to Semiarid Moisture Constraints",
      "mechanism": "Introducing drought-adapted leguminous cover crops fixes atmospheric nitrogen to enhance microbial C:N balance and build topsoil organic carbon. In semiarid regions where precipitation is limited, careful selection of cover crop species and growth windows avoids soil water competition with primary crops (Unger and Vigil, 1998).",
      "variable_interactions": [
        "Legume Nitrogen Fixation <-> Soil Microbial Carbon Stabilization",
        "Cover Crop Water Demand <-> Semiarid Available Soil Moisture",
        "Crop Diversification <-> Soil Biota Redundancy"
      ],
      "impacted_metrics": [
        "Topsoil Organic Carbon Stock (SOC)",
        "Available Soil Moisture Retention",
        "Soil Microbial Parameters"
      ],
      "estimated_effect": "Enhances soil organic carbon stocks while managing potential soil water competition in semiarid environments, improving water infiltration and aggregate stability.",
      "time_horizon": "short-term",
      "confidence": "high",
      "sources": [
        {
          "chunk_id": "4d894bde-2aef-5c18-9038-33512302261e",
          "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)",
          "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
          "year": 2021,
          "section_title": "Page 21",
          "page": 21,
          "url_or_doi": "https://doi.org/10.4060/cb6595en",
          "citation": "[Food and Agriculture Organization of the United Nations (FAO), 2021] Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems) (p. 21) [https://doi.org/10.4060/cb6595en]"
        }
      ]
    }
  ]
}
```

#### Human-Readable Text Format (`?format=text`):
**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/assess?format=text" \
  -H "Content-Type: application/json" \
  -d '{
    "land_use": "cropland",
    "soc_percent": 0.8,
    "rainfall_mm": 350.0,
    "region": "semi-arid"
  }'
```

**Actual Live Response (`200 OK`)**:
```markdown
Based on the multi-variable ecological profile of your site, here are targeted, scientifically grounded recommendations:

**Overall Assessment Confidence**: `MEDIUM`
*Overall assessment confidence is rated MEDIUM based on 2 peer-reviewed action(s) with verified page-level citations from FAO/IPCC/CBD literature and 4 missing ecological pillar(s).*

### 1. Integrate Multi-Species Agroforestry Hedgerows & Field Margins
**Ecological Mechanism**: Combining woody perennials with annual crops establishes structural diversity that buffers microclimates against heat extremes, reduces wind-driven evapotranspiration, and creates continuous ecological corridors for beneficial pollinator and predator taxa across monoculture landscapes.

**Cross-Variable Interactions & Synergies**:
- *Vegetation Structural Diversity <-> Microclimate Thermal Buffering*
- *Landscape Heterogeneity <-> Pollinator & Predator Abundance*
- *Tree Root Biomass <-> Deep Soil Carbon Stabilization*

**Impacted Metrics**: Field Evaporative Water Loss, Soil Organic Carbon in subsoil layers, Species Richness Proxy & Pollinator Density, Ecological Connectivity (CBD Target 10)
**Expected Outcome**: Increases carbon storage through combined aboveground and belowground tree biomass, enhances structural landscape heterogeneity, and advances biodiversity-friendly management.
**Implementation Horizon**: `medium-term` | **Scientific Confidence**: `HIGH`

**Scientific Evidence & Citations**:
- [Convention on Biological Diversity (CBD / UNEP), 2022] *CBD COP15 Decision 15/4: Kunming-Montreal Global Biodiversity Framework* (p. 4) (https://www.cbd.int/doc/decisions/cop-15/cop-15-dec-04-en.pdf)

### 2. Implement Seasonal Legume Cover Cropping Tailored to Semiarid Moisture Constraints
**Ecological Mechanism**: Introducing drought-adapted leguminous cover crops fixes atmospheric nitrogen to enhance microbial C:N balance and build topsoil organic carbon. In semiarid regions where precipitation is limited, careful selection of cover crop species and growth windows avoids soil water competition with primary crops (Unger and Vigil, 1998).

**Cross-Variable Interactions & Synergies**:
- *Legume Nitrogen Fixation <-> Soil Microbial Carbon Stabilization*
- *Cover Crop Water Demand <-> Semiarid Available Soil Moisture*
- *Crop Diversification <-> Soil Biota Redundancy*

**Impacted Metrics**: Topsoil Organic Carbon Stock (SOC), Available Soil Moisture Retention, Soil Microbial Parameters
**Expected Outcome**: Enhances soil organic carbon stocks while managing potential soil water competition in semiarid environments, improving water infiltration and aggregate stability.
**Implementation Horizon**: `short-term` | **Scientific Confidence**: `HIGH`

**Scientific Evidence & Citations**:
- [Food and Agriculture Organization of the United Nations (FAO), 2021] *Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)* (p. 21) (https://doi.org/10.4060/cb6595en)

---
*These recommendations are grounded in peer-reviewed protocols from FAO, IPCC AR6 WGII, and the CBD Kunming-Montreal Framework.*
```

---

## ⚠️ Known Limitations

1. **IPBES Source Exclusion**: The IPBES Global Assessment PDF was excluded from the local vector database due to persistent `403 Forbidden` responses on the Zenodo mirror. Terrestrial ecosystem and biodiversity risk coverage is fully substantiated via **IPCC AR6 WGII Chapter 2** and **CBD COP15 Decision 15/4**.
2. **Chunk Boundary Truncation**: In rare cases, complex multi-page data tables in the source FAO manual have quantitative estimates split across chunk boundaries.
3. **Heuristic Confidence Calibration**: The overall confidence calculation is calibrated against the 5-variable `data_completeness_score` and individual recommendation confidence scores rather than Bayesian posterior uncertainty.
4. **In-Memory Session Persistence**: The chat session store is maintained in-memory for the hackathon prototype and clears on server restart.

---
