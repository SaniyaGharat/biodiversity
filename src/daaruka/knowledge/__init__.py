"""Knowledge Module for Daaruka Biodiversity Intelligence Platform.

Exposes:
- `retrieve`: Semantic similarity search with citation metadata.
- `SoilGridsClient`: ISRIC SoilGrids REST API client.
- `GBIFClient`: GBIF Occurrence API client.
- `DocumentIngestionEngine`: Corpus parser and indexer.
- `VectorStore`: ChromaDB vector index manager.
- Models: `SourceCitation`, `RetrievedChunk`, `SoilProfile`, `BiodiversityMetrics`.
"""

from daaruka.knowledge.models import (
    SourceCitation,
    RetrievedChunk,
    KnowledgeSearchResponse,
    SoilProfile,
    SoilPropertyLayer,
    BiodiversityMetrics,
    ThreatenedSpeciesRecord,
)
from daaruka.knowledge.connectors import BaseConnector, SoilGridsClient, GBIFClient
from daaruka.knowledge.chunker import DocumentChunker
from daaruka.knowledge.vector_store import VectorStore, default_vector_store
from daaruka.knowledge.ingest import DocumentIngestionEngine
from daaruka.knowledge.retriever import retrieve, format_retrieval_context

__all__ = [
    "SourceCitation",
    "RetrievedChunk",
    "KnowledgeSearchResponse",
    "SoilProfile",
    "SoilPropertyLayer",
    "BiodiversityMetrics",
    "ThreatenedSpeciesRecord",
    "BaseConnector",
    "SoilGridsClient",
    "GBIFClient",
    "DocumentChunker",
    "VectorStore",
    "default_vector_store",
    "DocumentIngestionEngine",
    "retrieve",
    "format_retrieval_context",
]
