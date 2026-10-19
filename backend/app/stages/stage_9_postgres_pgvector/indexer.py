"""
STAGE 9: Ingestion & Vector Indexer for PostgreSQL + pgvector
------------------------------------------------------------
Extracts structured chunks from everyday_business_banking_guide.pdf,
generates text-embedding-3-small embeddings, and persists them into PostgreSQL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load .env BEFORE importing db.py: db.py reads DATABASE_URL at import time,
# otherwise it falls back to the default (localhost:5432) instead of Docker (5433).
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

from app.stages.stage_8_enterprise_ingestion.ingest_engine import (
    parse_banking_guide_pdf,
    chunk_banking_guide
)
from app.stages.stage_9_postgres_pgvector.db import SessionLocal, DocumentChunk, init_db

PDF_PATH = BACKEND_DIR / "docs" / "sample_data" / "everyday_business_banking_guide.pdf"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def index_banking_pdf_to_postgres():
    print("1. Initializing PostgreSQL tables and pgvector extension...")
    init_db()
    # Create a new session for database operations
    # Every time you want to interact with the database, you should create a new session.
    # The validity of the session is limited to the context of a single function or request.
    # When you ask followup questions, you should create a new session to query the database again.
    # when second quetion is continue quetions of first question then you should create a new session to query the database again.
    # Question when this session is useful, Why do I need to create a new session for every message? 
    # The session is useful for managing the database connection and transactions. It ensures that each operation is isolated and can be rolled back if an error occurs. Creating a new session for every message allows for better control over the database state and prevents potential conflicts or data corruption.
    # So, here session is not to maintain the state of the conversation, but to manage the database interactions effectively.
    session = SessionLocal()
    try:
        # Check if already indexed
        count = session.query(DocumentChunk).count()
        if count > 0:
            print(f"Database already contains {count} chunks. Skipping re-indexing.")
            return

        print(f"2. Parsing PDF from {PDF_PATH}...")
        pages = parse_banking_guide_pdf(PDF_PATH)
        chunks = chunk_banking_guide(pages, tenant_id="retail-business-banking")

        print(f"3. Extracted {len(chunks)} structured chunks. Generating embeddings...")
        texts = [c["text"] for c in chunks]

        emb_res = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        embeddings = [item.embedding for item in emb_res.data]

        print("4. Persisting chunks, metadata, and vectors into PostgreSQL...")
        for c, emb in zip(chunks, embeddings):
            db_chunk = DocumentChunk(
                chunk_id=c["chunk_id"],
                tenant_id=c["metadata"]["tenant_id"],
                document_name=c["metadata"]["source"],
                page_number=c["metadata"]["page_number"],
                section_title=c["metadata"]["section_title"],
                chunk_text=c["text"],
                embedding=emb
            )
            session.add(db_chunk)

        session.commit()
        print("Done! All chunks successfully loaded into PostgreSQL + pgvector.")

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()


if __name__ == "__main__":
    index_banking_pdf_to_postgres()