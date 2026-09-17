"""Programmatic PDF text extraction and ingestion engine with real page-boundary tracking."""

import os
import glob
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from pypdf import PdfReader

from daaruka.knowledge.chunker import DocumentChunker
from daaruka.knowledge.models import RetrievedChunk
from daaruka.knowledge.vector_store import VectorStore, default_vector_store

logger = logging.getLogger(__name__)

DOCUMENT_METADATA_REGISTRY: Dict[str, Dict[str, Any]] = {
    "cbd_cop15_dec_04.pdf": {
        "document_title": "CBD COP15 Decision 15/4: Kunming-Montreal Global Biodiversity Framework",
        "publisher": "Convention on Biological Diversity (CBD / UNEP)",
        "year": 2022,
        "topics": ["policy", "restoration", "biodiversity-targets", "conservation", "protected-areas"],
        "url_or_doi": "https://www.cbd.int/doc/decisions/cop-15/cop-15-dec-04-en.pdf",
    },
    "ipcc_ar6_wg2_chapter02.pdf": {
        "document_title": "IPCC AR6 WGII Chapter 2: Terrestrial and Freshwater Ecosystems and their Services",
        "publisher": "Intergovernmental Panel on Climate Change (IPCC)",
        "year": 2022,
        "topics": ["climate", "biodiversity", "ecosystems", "tipping-points", "resilience", "species-extinction"],
        "url_or_doi": "https://doi.org/10.1017/9781009325844.004",
    },
    "fao_recarbonizing_global_soils_vol3.pdf": {
        "document_title": "Recarbonizing Global Soils: A Technical Manual of Recommended Management Practices (Vol 3: Cropland & Grassland Systems)",
        "publisher": "Food and Agriculture Organization of the United Nations (FAO)",
        "year": 2021,
        "topics": ["soil", "carbon", "cover-cropping", "agriculture", "soc", "tillage", "soil-organic-carbon"],
        "url_or_doi": "https://doi.org/10.4060/cb6595en",
    },
}


class DocumentIngestionEngine:
    """Ingests real PDF documents into ChromaDB with programmatic page-boundary citations."""

    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        chunker: Optional[DocumentChunker] = None,
    ):
        self.vector_store = vector_store or default_vector_store
        self.chunker = chunker or DocumentChunker(chunk_size=750, chunk_overlap=120)

    def parse_pdf_file(self, file_path: str) -> List[RetrievedChunk]:
        """Extract text page-by-page from raw PDF, preserving exact physical page numbers."""
        filename = os.path.basename(file_path).lower()
        meta = DOCUMENT_METADATA_REGISTRY.get(filename, {
            "document_title": Path(file_path).stem.replace("_", " ").title(),
            "publisher": "Scientific Report",
            "year": 2022,
            "topics": ["environment", "biodiversity"],
            "url_or_doi": None,
        })

        reader = PdfReader(file_path)
        all_chunks: List[RetrievedChunk] = []

        logger.info(f"Extracting text from '{filename}' ({len(reader.pages)} pages)...")

        for page_idx, page in enumerate(reader.pages, start=1):
            try:
                text = page.extract_text() or ""
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_idx} of {filename}: {e}")
                continue

            clean_text = text.strip()
            # Skip empty pages or cover pages with minimal text
            if len(clean_text) < 50:
                continue

            # Programmatic chunking with real 1-indexed PDF page metadata
            page_chunks = self.chunker.chunk_section(
                section_text=clean_text,
                document_title=meta["document_title"],
                publisher=meta["publisher"],
                year=meta["year"],
                section_title=f"Page {page_idx}",
                topics=meta["topics"],
                page=page_idx,
                url_or_doi=meta.get("url_or_doi"),
            )
            all_chunks.extend(page_chunks)

        logger.info(f"Generated {len(all_chunks)} chunks with real page metadata from '{filename}'.")
        return all_chunks

    def ingest_directory(self, directory_path: str) -> Dict[str, Any]:
        """Scan raw directory, extract text from real PDFs, and upsert to ChromaDB."""
        if not os.path.exists(directory_path):
            raise FileNotFoundError(f"Raw data directory not found: {directory_path}")

        pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
        if not pdf_files:
            raise FileNotFoundError(f"No PDF files found in {directory_path}")

        all_chunks: List[RetrievedChunk] = []
        processed_files: List[str] = []

        for filepath in pdf_files:
            chunks = self.parse_pdf_file(filepath)
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
