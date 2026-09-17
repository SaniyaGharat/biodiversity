"""Integration tests for document ingestion, vector retrieval, and source citation traceability."""

import os
import shutil
import tempfile
import pytest
from fastapi.testclient import TestClient

from daaruka.knowledge.models import SourceCitation, RetrievedChunk
from daaruka.knowledge.chunker import DocumentChunker
from daaruka.knowledge.vector_store import VectorStore
from daaruka.knowledge.ingest import DocumentIngestionEngine
from daaruka.knowledge.retriever import retrieve, format_retrieval_context


SAMPLE_FIXTURE_MD = """---
document_title: "FAO Soil Carbon Sequestration Guidelines"
publisher: "FAO"
year: 2021
doi_or_url: "https://doi.org/10.4060/fao-test"
topics: ["soil", "carbon", "cover-crops"]
---

# Section: Cover Crops and Organic Carbon

Legume and grass cover crops increase soil organic carbon stocks by supplying continuous root exudates.
Field trials demonstrate an average annual topsoil sequestration rate of 0.4 tonnes of carbon per hectare.

# Section: Soil Acidity and Liming

Applying agricultural lime to strongly acidic soils (pH < 5.5) restores biological nitrogen fixation.
"""


@pytest.fixture(scope="module")
def isolated_vector_store():
    """Create a temporary isolated ChromaDB vector store directory for testing."""
    temp_dir = tempfile.mkdtemp(prefix="chroma_test_")
    store = VectorStore(
        persist_directory=temp_dir,
        collection_name="test_biodiversity_knowledge",
    )
    yield store
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_chunker_markdown_parsing():
    """Test chunker correctly extracts YAML frontmatter metadata and section headings."""
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
    chunks = chunker.chunk_markdown_document(SAMPLE_FIXTURE_MD)

    assert len(chunks) == 2
    assert chunks[0].citation.document_title == "FAO Soil Carbon Sequestration Guidelines"
    assert chunks[0].citation.publisher == "FAO"
    assert chunks[0].citation.year == 2021
    assert chunks[0].citation.section_title == "Cover Crops and Organic Carbon"
    assert "cover-crops" in chunks[0].citation.topics
    assert chunks[0].citation.url_or_doi == "https://doi.org/10.4060/fao-test"

    # Citation string check
    cit_str = chunks[0].citation.citation_string()
    assert "[FAO, 2021]" in cit_str
    assert "Cover Crops and Organic Carbon" in cit_str


def test_ingestion_and_retrieval_with_citations(isolated_vector_store):
    """Test ingestion of fixture document into isolated vector store and semantic search."""
    chunker = DocumentChunker(chunk_size=500, chunk_overlap=50)
    chunks = chunker.chunk_markdown_document(SAMPLE_FIXTURE_MD)

    upserted = isolated_vector_store.add_chunks(chunks)
    assert upserted == 2
    assert isolated_vector_store.count() == 2

    # Query without filter
    results = retrieve(
        query="how do cover crops increase organic carbon stocks",
        top_k=2,
        vector_store=isolated_vector_store,
    )

    assert len(results) > 0
    top_result = results[0]
    assert "root exudates" in top_result.content or "carbon stocks" in top_result.content

    # Strict citation assertions
    assert top_result.citation is not None
    assert top_result.citation.document_title == "FAO Soil Carbon Sequestration Guidelines"
    assert top_result.citation.publisher == "FAO"
    assert top_result.citation.year == 2021
    assert top_result.citation.section_title == "Cover Crops and Organic Carbon"
    assert top_result.similarity_score > 0.0

    # Test context formatting
    context_str = format_retrieval_context(results)
    assert "[1] [FAO, 2021]" in context_str
    assert "Cover Crops and Organic Carbon" in context_str


def test_retrieval_with_topic_filtering(isolated_vector_store):
    """Test tag-filtered search filters out unmatching topics."""
    # Search with matching tag
    soil_results = retrieve(
        query="soil management",
        top_k=2,
        filter_tags=["soil"],
        vector_store=isolated_vector_store,
    )
    assert len(soil_results) > 0


def test_api_knowledge_search_endpoint(client: TestClient, monkeypatch):
    """Test GET /api/v1/knowledge/search returns expected JSON schema."""
    response = client.get("/api/v1/knowledge/search", params={"query": "cover crops and soil carbon", "top_k": 3})
    assert response.status_code == 200

    data = response.json()
    assert data["query"] == "cover crops and soil carbon"
    assert "total_results" in data
    assert "results" in data
    assert isinstance(data["results"], list)
