"""ChromaDB Vector Store management for biodiversity knowledge chunks."""

import os
import logging
from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings
from chromadb.utils import embedding_functions

from daaruka.core.config import settings
from daaruka.knowledge.models import RetrievedChunk, SourceCitation

logger = logging.getLogger(__name__)


class VectorStore:
    """Encapsulates ChromaDB persistent client, embedding generation, and metadata retrieval."""

    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: Optional[str] = None,
    ):
        self.persist_directory = persist_directory or settings.CHROMA_PERSIST_DIRECTORY
        self.collection_name = collection_name or settings.CHROMA_COLLECTION_NAME

        # Ensure directory exists
        os.makedirs(self.persist_directory, exist_ok=True)

        # Initialize persistent Chroma client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=ChromaSettings(anonymized_telemetry=False),
        )

        # Initialize local fast ONNX embedding function (MiniLM-L6-v2)
        self.embedding_fn = embedding_functions.DefaultEmbeddingFunction()

        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )

    def add_chunks(self, chunks: List[RetrievedChunk]) -> int:
        """Embed and upsert chunks with flattened metadata into ChromaDB collection."""
        if not chunks:
            return 0

        ids: List[str] = []
        documents: List[str] = []
        metadatas: List[Dict[str, Any]] = []

        for chunk in chunks:
            ids.append(chunk.chunk_id)
            documents.append(chunk.content)

            # Flatten citation metadata for ChromaDB compatibility
            c = chunk.citation
            topics_csv = ",".join(t.lower().strip() for t in c.topics) if c.topics else ""
            meta = {
                "document_title": c.document_title,
                "publisher": c.publisher,
                "year": c.year,
                "section_title": c.section_title,
                "page": c.page if c.page is not None else -1,
                "topics_csv": topics_csv,
                "url_or_doi": c.url_or_doi or "",
            }
            metadatas.append(meta)

        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
        )
        logger.info(f"Upserted {len(chunks)} chunks into collection '{self.collection_name}'.")
        return len(chunks)

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        filter_tags: Optional[List[str]] = None,
    ) -> List[RetrievedChunk]:
        """Perform semantic similarity search, unpacking metadata into strict SourceCitations."""
        total_items = self.collection.count()
        if total_items == 0:
            return []

        # If filtering tags, retrieve a wider candidate pool to allow tag filtering
        query_k = min(total_items, max(top_k * 4, 10)) if filter_tags else min(total_items, top_k)

        results = self.collection.query(
            query_texts=[query_text],
            n_results=query_k,
        )

        retrieved_chunks: List[RetrievedChunk] = []

        ids_list = results.get("ids", [[]])[0]
        docs_list = results.get("documents", [[]])[0]
        metas_list = results.get("metadatas", [[]])[0]
        distances = results.get("distances", [[]])[0] if "distances" in results else []

        target_tags = [t.lower().strip() for t in filter_tags] if filter_tags else None

        for idx, chunk_id in enumerate(ids_list):
            content = docs_list[idx]
            meta = metas_list[idx]

            # Reconstruct topics
            topics = [t.strip() for t in meta.get("topics_csv", "").split(",") if t.strip()]

            # Apply tag filter if specified
            if target_tags:
                topics_lower = [t.lower() for t in topics]
                if not any(tt in topics_lower for tt in target_tags):
                    continue

            # Cosine distance to similarity: similarity = 1 - distance
            dist = distances[idx] if idx < len(distances) else 0.0
            similarity = max(0.0, min(1.0, 1.0 - dist))

            page_val = meta.get("page")
            page = int(page_val) if page_val is not None and page_val != -1 else None

            citation = SourceCitation(
                document_title=meta.get("document_title", "Unknown"),
                publisher=meta.get("publisher", "Unknown"),
                year=int(meta.get("year", 2024)),
                section_title=meta.get("section_title", "General"),
                page=page,
                topics=topics,
                url_or_doi=meta.get("url_or_doi") or None,
            )

            retrieved_chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    content=content,
                    similarity_score=round(similarity, 4),
                    citation=citation,
                )
            )

            if len(retrieved_chunks) >= top_k:
                break

        return retrieved_chunks

    def count(self) -> int:
        """Return total chunks count in collection."""
        return self.collection.count()

    def clear(self) -> None:
        """Clear all records in the collection."""
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
            metadata={"hnsw:space": "cosine"},
        )


# Global default vector store instance
default_vector_store = VectorStore()
