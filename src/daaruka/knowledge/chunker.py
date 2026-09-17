"""Semantic text chunker preserving section hierarchy and citation metadata."""

import re
import uuid
from typing import List, Dict, Any, Optional
from daaruka.knowledge.models import SourceCitation, RetrievedChunk


class DocumentChunker:
    """Splits structured ecological documents into semantic chunks with attached citations."""

    def __init__(self, chunk_size: int = 700, chunk_overlap: int = 120):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_section(
        self,
        section_text: str,
        document_title: str,
        publisher: str,
        year: int,
        section_title: str,
        topics: List[str],
        page: Optional[int] = None,
        url_or_doi: Optional[str] = None,
    ) -> List[RetrievedChunk]:
        """Split a single document section into overlapping semantic chunks with citations."""
        clean_text = section_text.strip()
        if not clean_text:
            return []

        chunks: List[RetrievedChunk] = []

        # If text is smaller than chunk_size, emit as single chunk
        if len(clean_text) <= self.chunk_size:
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_title}_{section_title}_0"))
            citation = SourceCitation(
                document_title=document_title,
                publisher=publisher,
                year=year,
                section_title=section_title,
                page=page,
                topics=topics,
                url_or_doi=url_or_doi,
            )
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    content=clean_text,
                    similarity_score=1.0,
                    citation=citation,
                )
            )
            return chunks

        # Split text into paragraphs first
        paragraphs = clean_text.split("\n\n")
        current_chunk = ""
        chunk_idx = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_chunk) + len(para) + 2 <= self.chunk_size:
                current_chunk = f"{current_chunk}\n\n{para}".strip()
            else:
                if current_chunk:
                    chunk_id = str(
                        uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_title}_{section_title}_{chunk_idx}")
                    )
                    citation = SourceCitation(
                        document_title=document_title,
                        publisher=publisher,
                        year=year,
                        section_title=section_title,
                        page=page,
                        topics=topics,
                        url_or_doi=url_or_doi,
                    )
                    chunks.append(
                        RetrievedChunk(
                            chunk_id=chunk_id,
                            content=current_chunk,
                            similarity_score=1.0,
                            citation=citation,
                        )
                    )
                    chunk_idx += 1

                # If paragraph itself is longer than chunk_size, split by sentences/window
                if len(para) > self.chunk_size:
                    start = 0
                    while start < len(para):
                        end = min(start + self.chunk_size, len(para))
                        sub_text = para[start:end]
                        chunk_id = str(
                            uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_title}_{section_title}_{chunk_idx}")
                        )
                        citation = SourceCitation(
                            document_title=document_title,
                            publisher=publisher,
                            year=year,
                            section_title=section_title,
                            page=page,
                            topics=topics,
                            url_or_doi=url_or_doi,
                        )
                        chunks.append(
                            RetrievedChunk(
                                chunk_id=chunk_id,
                                content=sub_text,
                                similarity_score=1.0,
                                citation=citation,
                            )
                        )
                        chunk_idx += 1
                        start += self.chunk_size - self.chunk_overlap
                    current_chunk = ""
                else:
                    current_chunk = para

        if current_chunk:
            chunk_id = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{document_title}_{section_title}_{chunk_idx}"))
            citation = SourceCitation(
                document_title=document_title,
                publisher=publisher,
                year=year,
                section_title=section_title,
                page=page,
                topics=topics,
                url_or_doi=url_or_doi,
            )
            chunks.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    content=current_chunk,
                    similarity_score=1.0,
                    citation=citation,
                )
            )

        return chunks

    def chunk_markdown_document(self, content: str) -> List[RetrievedChunk]:
        """Parse frontmatter and markdown sections with '# Section: ...' headings."""
        doc_title = "Untitled Document"
        publisher = "General"
        year = 2024
        doi_or_url = None
        topics = []

        # Parse YAML-like frontmatter if present
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                frontmatter_text = parts[1]
                content = parts[2]
                for line in frontmatter_text.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip().lower()
                        v = v.strip().strip('"').strip("'")
                        if k == "document_title":
                            doc_title = v
                        elif k == "publisher":
                            publisher = v
                        elif k == "year":
                            try:
                                year = int(v)
                            except ValueError:
                                pass
                        elif k in ("doi_or_url", "url", "doi"):
                            doi_or_url = v
                        elif k == "topics":
                            # Parse JSON or comma list
                            cleaned_v = v.strip("[]")
                            topics = [t.strip().strip('"').strip("'") for t in cleaned_v.split(",") if t.strip()]

        # Split on section headings
        section_pattern = re.compile(r"^#+\s+(?:Section:?\s*)?(.*)$", re.MULTILINE)
        sections = section_pattern.split(content)

        all_chunks: List[RetrievedChunk] = []

        if len(sections) == 1:
            # No section headers
            return self.chunk_section(
                section_text=sections[0],
                document_title=doc_title,
                publisher=publisher,
                year=year,
                section_title="Introduction & Overview",
                topics=topics,
                url_or_doi=doi_or_url,
            )

        # sections[0] is text before first heading, sections[1] is 1st heading, sections[2] is 1st body, etc.
        intro_text = sections[0].strip()
        if intro_text:
            all_chunks.extend(
                self.chunk_section(
                    section_text=intro_text,
                    document_title=doc_title,
                    publisher=publisher,
                    year=year,
                    section_title="Overview",
                    topics=topics,
                    url_or_doi=doi_or_url,
                )
            )

        for i in range(1, len(sections), 2):
            sec_heading = sections[i].strip()
            sec_body = sections[i + 1].strip() if (i + 1) < len(sections) else ""
            if sec_body:
                all_chunks.extend(
                    self.chunk_section(
                        section_text=sec_body,
                        document_title=doc_title,
                        publisher=publisher,
                        year=year,
                        section_title=sec_heading,
                        topics=topics,
                        url_or_doi=doi_or_url,
                    )
                )

        return all_chunks
