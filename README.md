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
│   │   - `POST /api/v1/knowledge/search` (Grounded semantic & topic retrieval)      │   │
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

**Example Response (`200 OK`)**:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2026-09-17T22:45:00.000000",
  "services": {
    "api": "operational",
    "vector_store": "ready",
    "connectors": "ready"
  }
}
```

---

### 2. Semantic Knowledge Search
`POST /api/v1/knowledge/search`

Search the grounded knowledge base with optional topic filtering (`soil`, `climate`, `restoration`, `policy`).

**Example Request**:
```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "soil organic carbon cover cropping sequestration rate",
    "n_results": 2,
    "topic": "soil"
  }'
```

**Example Response (`200 OK`)**:
```json
[
  {
    "chunk_id": "4d894bde-2aef-5c18-9038-33512302261e",
    "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3)",
    "page_number": 21,
    "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
    "year": 2021,
    "text": "Crop rotation with cover crops can increase soil organic carbon...",
    "topics": ["soil", "carbon", "cover-cropping"],
    "score": 0.88,
    "url_or_doi": "https://doi.org/10.4060/cb6595en"
  }
]
```

---

### 3. Multi-Turn Conversational Chat
`POST /api/v1/chat`

Handles free-text input, extracts ecological parameters, maintains multi-turn session state, asks non-repeating clarifying questions for missing data, and generates grounded recommendations.

**Example Request (Turn 1 - Partial Input)**:
```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "field_demo_01",
    "message": "I manage 50 hectares of cropland with sandy soil and 0.8% organic carbon in a semi-arid zone."
  }'
```

**Example Response (`200 OK`)**:
```json
{
  "session_id": "field_demo_01",
  "response": "### 🌿 Ecological Site Assessment & Recommendations\n\n**Data Completeness:** 60.0%\n**Overall Confidence:** Medium\n\n#### 🌾 Recommended Interventions\n1. **High-Residue Cover Cropping & Organic Amendment**\n   - **Rationale:** Addresses severe SOC deficit (0.8%) in semi-arid cropland.\n   - **Evidence:** *FAO Recarbonizing Global Soils Vol 3 (p. 21)*\n\n#### ❓ Clarifying Questions for Higher Confidence\n- What is the typical annual rainfall (mm) or moisture regime at the site?",
  "extracted_parameters": {
    "land_use": "cropland",
    "soc_percent": 0.8,
    "region": "semi-arid"
  },
  "missing_parameters": ["rainfall_mm", "latitude/longitude"],
  "clarifying_question": "What is the typical annual rainfall (mm) or moisture regime at the site?",
  "data_completeness_score": 0.6
}
```

---

### 4. Structured Assessment & Geo-Enrichment
`POST /api/v1/assess`

Programmatic evaluation endpoint accepting structured `SiteAssessmentInput` JSON. Automatically queries **SoilGrids** and **GBIF** when coordinates (`latitude`, `longitude`) are provided. Supports `?format=json` (default) and `?format=text`.

**Example Request (JSON format with Coordinates)**:
```bash
curl -X POST "http://localhost:8000/api/v1/assess?format=json" \
  -H "Content-Type: application/json" \
  -d '{
    "land_use": "cropland",
    "soc_percent": 0.8,
    "rainfall_mm": 350.0,
    "region": "semi-arid",
    "latitude": -1.286389,
    "longitude": 36.817223
  }'
```

**Example Response (`200 OK`)**:
```json
{
  "gap_analysis": {
    "missing_fields": [],
    "completeness_score": 1.0,
    "suggested_questions": []
  },
  "overall_confidence": "high",
  "confidence_rationale": "High data completeness (100.0%) with comprehensive multi-variable observations.",
  "recommendations": [
    {
      "title": "High-Residue Cover Cropping & Organic Residue Retention",
      "target_variable": "Soil Organic Carbon & Moisture Retention",
      "action": "Integrate drought-tolerant legume cover crops during fallow periods and maintain >30% surface crop residue.",
      "estimated_effect": "Increases SOC sequestration by up to 0.32–0.55 t C/ha/yr and improves moisture retention.",
      "interacting_variables": ["soc_percent (0.8%)", "rainfall_mm (350.0mm)", "land_use (cropland)"],
      "confidence": "high",
      "sources": [
        {
          "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)",
          "page_number": 21,
          "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
          "year": 2021,
          "chunk_id": "4d894bde-2aef-5c18-9038-33512302261e",
          "url_or_doi": "https://doi.org/10.4060/cb6595en"
        }
      ]
    }
  ],
  "species_richness_proxy": 142,
  "evaluated_inputs": {
    "land_use": "cropland",
    "soc_percent": 0.8,
    "ph": 6.2,
    "rainfall_mm": 350.0,
    "region": "semi-arid",
    "latitude": -1.286389,
    "longitude": 36.817223
  }
}
```

**Example Request (`?format=text`)**:
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

---

## ⚠️ Known Limitations

1. **IPBES Source Exclusion**: The IPBES Global Assessment PDF was excluded from the local vector database due to persistent `403 Forbidden` responses on the Zenodo mirror. Terrestrial ecosystem and biodiversity risk coverage is fully substantiated via **IPCC AR6 WGII Chapter 2** and **CBD COP15 Decision 15/4**.
2. **Chunk Boundary Truncation**: In rare cases, complex multi-page data tables in the source FAO manual have quantitative estimates split across chunk boundaries.
3. **Heuristic Confidence Calibration**: The overall confidence calculation is calibrated against the 5-variable `data_completeness_score` and individual recommendation confidence scores rather than Bayesian posterior uncertainty.
4. **In-Memory Session Persistence**: The chat session store is maintained in-memory for the hackathon prototype and clears on server restart.

---

## 👥 Repository & Collaborators

- **Repository**: [https://github.com/SaniyaGharat/biodiversity](https://github.com/SaniyaGharat/biodiversity) (Public)
- **Hackathon Evaluation Collaborators**:
  - `ankita.dasgupta@darukaa.com`
  - `harsh.kumar@darukaa.com`
  - `utkarsh.gauniyal@darukaa.com`
  - `guneet.mutreja@darukaa.com`
