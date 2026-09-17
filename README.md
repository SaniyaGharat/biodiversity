# 🌿 Daaruka.Earth: Biodiversity Intelligence Chatbot

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-green.svg)](https://fastapi.tiangolo.com/)
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen.svg)]()

An AI-powered Biodiversity Intelligence platform built for the **Darukaa.Earth** hackathon. The system integrates multi-dimensional ecological datasets (soil health, species occurrence, land cover, climate variability, and human footprint) into a grounded reasoning engine and conversational intelligence layer.

---

## 🏛️ System Architecture

```
                               ┌────────────────────────────────────────┐
                               │           Client / Frontend            │
                               │    (Web App, Chatbot UI, REST API)    │
                               └───────────────────┬────────────────────┘
                                                   │
                                                   ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FastAPI Application                                  │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                              API Layer (`api/`)                                │   │
│   │   - `/health` & `/api/v1/health`                                               │   │
│   │   - `/api/v1/chat` (Conversational streaming & multi-turn dialog)              │   │
│   │   - `/api/v1/intelligence/query` (Structured JSON multi-metric evaluation)     │   │
│   └───────────────────────┬────────────────────────────────┬───────────────────────┘   │
│                           │                                │                           │
│                           ▼                                ▼                           │
│   ┌───────────────────────────────────┐    ┌───────────────────────────────────────┐   │
│   │        Chat Layer (`chat/`)       │    │     Reasoning Engine (`reasoning/`)   │   │
│   │  - Dialog state & short-term mem  │    │  - Soil Health index calculation      │   │
│   │  - Context routing & templating   │◄───┤  - Biodiversity threat score (IUCN)   │   │
│   │  - Evidence attribution citation  │    │  - LULC fragmentation analysis        │   │
│   └─────────────────┬─────────────────┘    │  - Climate & Human stress metrics     │   │
│                     │                      └───────────────────┬───────────────────┘   │
│                     ▼                                          ▼                       │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │                           Knowledge Layer (`knowledge/`)                       │   │
│   │   - Ingestion pipelines for ISRIC SoilGrids, GBIF, Copernicus, WorldClim, SEDAC│   │
│   │   - Document chunking, metadata extraction & embedding                         │   │
│   │   - Vector DB indexing (ChromaDB) & Hybrid retrieval (Dense + Sparse/BM25)     │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 📦 Project Structure

```
daaruka/
├── src/
│   └── daaruka/
│       ├── __init__.py
│       ├── main.py                  # FastAPI factory, middleware, top-level routes
│       ├── core/
│       │   ├── __init__.py
│       │   └── config.py            # App settings (Pydantic BaseSettings, .env)
│       ├── api/                     # API routing & serialization
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py
│       │       ├── router.py        # Aggregated v1 API router
│       │       └── health.py        # Healthcheck endpoint
│       ├── knowledge/               # Phase 1: Data ingestion & RAG retrieval
│       │   └── __init__.py
│       ├── reasoning/               # Phase 2: Multi-metric biodiversity reasoning
│       │   └── __init__.py
│       └── chat/                    # Phase 3: Conversational engine & memory
│           └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # Pytest fixtures & TestClient configuration
│   └── test_health.py               # Healthcheck test suite
├── docs/
│   └── data_sources.md              # Detailed citable open dataset catalog
├── .env.example                     # Environment template
├── .gitignore                       # Git ignore configuration
├── pyproject.toml                   # Project metadata & build configuration
├── requirements.txt                 # Production & dev dependencies
├── pytest.ini                       # Pytest execution settings
└── README.md                        # Documentation & setup guide
```

---

## 🌐 Open Datasets Sourced

The platform synthesizes data across five core ecological dimensions (detailed in [`docs/data_sources.md`](docs/data_sources.md)):

1. **Soil Health**: [ISRIC SoilGrids250m](https://www.isric.org/explore/soilgrids) / FAO HWSD v2.0 *(REST API & GeoTIFF)*
2. **Biodiversity Indicators**: [GBIF Occurrence & Species API](https://www.gbif.org/) + IUCN Red List *(REST API & Darwin Core)*
3. **Land Use & Land Cover**: [Copernicus Global Land Service (LC100)](https://land.copernicus.eu/) / ESA WorldCover *(STAC API & Cloud-Optimized GeoTIFF)*
4. **Climate Factors**: [WorldClim v2.1](https://www.worldclim.org/) & ERA5-Land ECMWF *(CDS API & GeoTIFF)*
5. **Human Impact**: [Global Human Modification (GHM)](https://sedac.ciesin.columbia.edu/) & Human Footprint *(NASA SEDAC REST / GeoTIFF)*
6. **Synthesis & Benchmarks**: [IPCC AR6 WGII](https://www.ipcc.ch/) & IPBES Global Assessment *(DDC Data & Reports)*

---

## 🚀 Quickstart & Local Setup

### 1. Prerequisites
- Python 3.10+
- `pip` or `uv`

### 2. Installation
```bash
# Clone the repository
git clone https://github.com/your-org/daaruka.git
cd daaruka

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate    # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration
```bash
cp .env.example .env
```

### 4. Run the API Server
```bash
uvicorn src.daaruka.main:app --reload --host 0.0.0.0 --port 8000
```
- Interactive Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- ReDoc UI: [http://localhost:8000/redoc](http://localhost:8000/redoc)
- Health Check: [http://localhost:8000/health](http://localhost:8000/health)

---

## 🧪 Testing

Run the test suite with `pytest`:

```bash
pytest
```

---

## 🗺️ Implementation Roadmap

- [x] **Phase 0: Scaffolding & Data Sourcing** — FastAPI skeleton, project layout, datasets catalog, health check suite.
- [ ] **Phase 1: Knowledge Module (RAG & Ingestion)** — Data connectors for SoilGrids/GBIF, ChromaDB vector store, semantic chunking.
- [ ] **Phase 2: Multi-Metric Reasoning Engine** — Automated computation of Soil Health, Biodiversity Threat, LULC Fragmentation, and Climate Stress.
- [ ] **Phase 3: Conversational Intelligence & Memory** — Multi-turn chat memory, prompt synthesis with citations and source groundings.
- [ ] **Phase 4: API & Client Integration** — Streaming chat endpoints, structured JSON input/output evaluation endpoints, validation.
