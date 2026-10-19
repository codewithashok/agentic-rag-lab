"""
STAGE 8: Ingestion Engine for Everyday Business Banking Guide
------------------------------------------------------------
- Parses the plain-language banking PDF page-by-page.
- Splits chunks cleanly using the numbered headers (e.g., '3. Example payment limits').
- Enriches every chunk with enterprise metadata (page number, section title, tenant_id).
"""

import re
from pathlib import Path
from typing import List, Dict, Any
from pypdf import PdfReader


def parse_banking_guide_pdf(pdf_path: Path) -> List[Dict[str, Any]]:
    """Reads the PDF page-by-page and extracts raw text with page numbers."""
    reader = PdfReader(str(pdf_path))
    pages_data = []

    for idx, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages_data.append({
            "page_number": idx + 1,
            "raw_text": text
        })

    return pages_data

# This is just text reorganization and chunking, not embedding or vectorization.
# The enriched chunks can be used for downstream tasks like embedding, retrieval, or question-answering.
def chunk_banking_guide(
    pages_data: List[Dict[str, Any]],
    document_name: str = "everyday_business_banking_guide.pdf",
    tenant_id: str = "retail-business-banking"
) -> List[Dict[str, Any]]:
    """
    Splits text across pages into clean chunks bounded by the numbered section titles.
    Preserves tables and attaches metadata to each chunk.
    """
    enriched_chunks = []
    # Matches headers like: "1. What is this guide about?", "5. What fees might apply?", etc.
    header_pattern = re.compile(r"^(\d+\.\s+[A-Za-z0-9\s\?]+)$")

    current_section = "About this guide"

    for page in pages_data:
        page_num = page["page_number"]
        page_text = page["raw_text"]

        lines = [line.strip() for line in page_text.split("\n") if line.strip()]
        buffer = []

        for line in lines:
            header_match = header_pattern.match(line)
            if header_match:
                # Flush the prior section buffer if it has meaningful content
                if buffer:
                    chunk_text = "\n".join(buffer).strip()
                    if len(chunk_text) > 40:
                        enriched_chunks.append({
                            "chunk_id": f"{document_name}-p{page_num}-{len(enriched_chunks)}",
                            "text": chunk_text,
                            "metadata": {
                                "source": document_name,
                                "page_number": page_num,
                                "section_title": current_section,
                                "tenant_id": tenant_id,
                                "document_type": "Banking Guide"
                            }
                        })
                    buffer = []
                current_section = header_match.group(1).strip()

            buffer.append(line)

        # Flush whatever is left on the page
        if buffer:
            chunk_text = "\n".join(buffer).strip()
            if len(chunk_text) > 40:
                enriched_chunks.append({
                    "chunk_id": f"{document_name}-p{page_num}-{len(enriched_chunks)}",
                    "text": chunk_text,
                    "metadata": {
                        "source": document_name,
                        "page_number": page_num,
                        "section_title": current_section,
                        "tenant_id": tenant_id,
                        "document_type": "Banking Guide"
                    }
                })

    return enriched_chunks