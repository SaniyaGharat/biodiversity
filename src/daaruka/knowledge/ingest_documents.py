"""Standalone CLI script to re-run real PDF corpus ingestion into ChromaDB."""

import os
import sys
import argparse
import logging
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(BASE_DIR / "src"))

from daaruka.knowledge.ingest import DocumentIngestionEngine
from daaruka.knowledge.vector_store import default_vector_store

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("daaruka.ingest_documents")


def main():
    parser = argparse.ArgumentParser(description="Ingest real scientific PDF reports into ChromaDB.")
    parser.add_argument(
        "--raw-dir",
        type=str,
        default=str(BASE_DIR / "data" / "raw"),
        help="Path to the directory containing raw PDF reports (default: data/raw)",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Clear existing collection before ingesting",
    )
    args = parser.parse_args()

    raw_path = os.path.abspath(args.raw_dir)
    logger.info(f"Target raw PDFs directory: {raw_path}")

    if args.reset:
        logger.warning("Resetting existing ChromaDB knowledge collection...")
        default_vector_store.clear()

    engine = DocumentIngestionEngine(vector_store=default_vector_store)
    stats = engine.ingest_directory(raw_path)

    logger.info("Ingestion of real PDF documents complete!")
    logger.info(f"  Files processed: {stats['processed_files_count']} ({', '.join(stats['files'])})")
    logger.info(f"  Chunks created:   {stats['total_chunks_created']}")
    logger.info(f"  Total in DB:      {stats['total_collection_count']}")


if __name__ == "__main__":
    main()
