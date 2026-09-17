"""Document ingestion engine for parsing PDF and Markdown corpora into ChromaDB."""

import os
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    from pypdf import PdfReader
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

from daaruka.knowledge.chunker import DocumentChunker
from daaruka.knowledge.models import RetrievedChunk
from daaruka.knowledge.vector_store import VectorStore, default_vector_store

logger = logging.getLogger(__name__)


class DocumentIngestionEngine:
    """Ingests and indexes authoritative environmental documents into vector store."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        chunker: Optional[DocumentChunker] = None,
    ):
        self.vector_store = vector_store or default_vector_store
        self.chunker = chunker or DocumentChunker()

    def parse_pdf(self, file_path: str, default_metadata: Optional[Dict[str, Any]] = None) -> List[RetrievedChunk]:
        """Extract text from PDF pages and generate chunked records with page citations."""
        if not PYPDF_AVAILABLE:
            raise ImportError("pypdf is required for PDF parsing. Install with `pip install pypdf`.")

        reader = PdfReader(file_path)
        meta = default_metadata or {}
        doc_title = meta.get("document_title", Path(file_path).stem.replace("_", " ").title())
        publisher = meta.get("publisher", "Scientific Report")
        year = meta.get("year", 2024)
        topics = meta.get("topics", ["biodiversity", "environment"])
        url_or_doi = meta.get("url_or_doi")

        all_chunks: List[RetrievedChunk] = []

        for page_idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text()
            if not text or not text.strip():
                continue

            page_chunks = self.chunker.chunk_section(
                section_text=text,
                document_title=doc_title,
                publisher=publisher,
                year=year,
                section_title=f"Page {page_idx}",
                topics=topics,
                page=page_idx,
                url_or_doi=url_or_doi,
            )
            all_chunks.extend(page_chunks)

        return all_chunks

    def parse_markdown(self, file_path: str) -> List[RetrievedChunk]:
        """Parse markdown file containing frontmatter metadata and section headings."""
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        return self.chunker.chunk_markdown_document(content)

    def ingest_file(self, file_path: str) -> List[RetrievedChunk]:
        """Parse a single PDF or Markdown file and return generated chunks."""
        ext = os.path.splitext(file_path)[1].lower()
        if ext in (".md", ".markdown", ".txt"):
            return self.parse_markdown(file_path)
        elif ext == ".pdf":
            return self.parse_pdf(file_path)
        else:
            logger.warning(f"Unsupported file format '{ext}' for file {file_path}")
            return []

    def ingest_directory(self, directory_path: str) -> Dict[str, Any]:
        """Recursively scan directory, parse all supported documents, and upsert to vector store."""
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Corpus directory not found: {directory_path}")

        all_chunks: List[RetrievedChunk] = []
        processed_files: List[str] = []

        patterns = ["*.md", "*.markdown", "*.txt", "*.pdf"]
        for pattern in patterns:
            for filepath in glob.glob(os.path.join(directory_path, "**", pattern), recursive=True):
                chunks = self.ingest_file(filepath)
                all_chunks.extend(chunks)
                processed_files.append(os.path.basename(filepath))

        total_upserted = self.vector_store.add_chunks(all_chunks)

        return {
            "processed_files_count": len(processed_files),
            "files": processed_files,
            "total_chunks_created": len(all_chunks),
            "total_upserted": total_upserted,
            "total_collection_count": self.vector_store.count(),
        }
