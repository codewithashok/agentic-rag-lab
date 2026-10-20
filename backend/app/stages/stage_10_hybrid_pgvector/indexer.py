"""
STAGE 10: Ingestion for Hybrid PostgreSQL Table
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

from openai import OpenAI
from app.stages.stage_8_enterprise_ingestion.ingest_engine import (
    parse_banking_guide_pdf,
    chunk_banking_guide
)
from app.stages.stage_10_hybrid_pgvector.db_schema import (
    SessionLocal, DocumentChunkHybrid, upgrade_db_schema
)

PDF_PATH = BACKEND_DIR / "docs" / "sample_data" / "everyday_business_banking_guide.pdf"
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def seed_hybrid_table():
    print("1. Initializing Stage 10 hybrid schema and triggers...")
    upgrade_db_schema()

    session = SessionLocal()
    try:
        count = session.query(DocumentChunkHybrid).count()
        if count > 0:
            print(f"Hybrid table already has {count} chunks. Skipping re-index.")
            return

        print(f"2. Parsing {PDF_PATH}...")
        pages = parse_banking_guide_pdf(PDF_PATH)
        chunks = chunk_banking_guide(pages, tenant_id="retail-business-banking")

        print("3. Generating embeddings...")
        texts = [c["text"] for c in chunks]
        emb_res = client.embeddings.create(model="text-embedding-3-small", input=texts)
        embeddings = [item.embedding for item in emb_res.data]

        print("4. Persisting into banking_document_chunks_hybrid...")
        for c, emb in zip(chunks, embeddings):
            row = DocumentChunkHybrid(
                chunk_id=f"stage10-{c['chunk_id']}",
                tenant_id=c["metadata"]["tenant_id"],
                document_name=c["metadata"]["source"],
                page_number=c["metadata"]["page_number"],
                section_title=c["metadata"]["section_title"],
                chunk_text=c["text"],
                embedding=emb
            )
            session.add(row)

        session.commit()
        print("Done! Hybrid PostgreSQL table is populated.")
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    seed_hybrid_table()