"""
STAGE 10: PostgreSQL Schema with pgvector + tsvector Full-Text Search
---------------------------------------------------------------------
Adds a native tsvector column with a GIN index to banking_document_chunks
to enable native Hybrid Search (Keyword + Dense Vector) in SQL.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Index, text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.dialects.postgresql import TSVECTOR
from pgvector.sqlalchemy import Vector

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:postgres@localhost:5432/agentic_rag_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DocumentChunkHybrid(Base):
    __tablename__ = "banking_document_chunks_hybrid"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(120), unique=True, nullable=False)
    tenant_id = Column(String(50), index=True, nullable=False)
    document_name = Column(String(100), nullable=False)
    page_number = Column(Integer, nullable=False)
    section_title = Column(String(150), nullable=False)
    chunk_text = Column(Text, nullable=False)

    # 1. Native Dense Vector (1536 dims)
    embedding = Column(Vector(1536), nullable=False)

    # 2. Native Sparse Full-Text Search Vector
    search_vector = Column(TSVECTOR)


# HNSW Index for Dense Vector cosine similarity
Index(
    "idx_hybrid_embedding_hnsw",
    DocumentChunkHybrid.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"}
)

# GIN Index for Sparse Full-Text Search
Index(
    "idx_hybrid_search_vector_gin",
    DocumentChunkHybrid.search_vector,
    postgresql_using="gin"
)


def upgrade_db_schema():
    """Enables extensions and configures auto-updating tsvector trigger."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()

    Base.metadata.create_all(bind=engine)

    # Auto-generate tsvector from chunk_text using PostgreSQL english dictionary
    with engine.connect() as conn:
        conn.execute(text("""
            CREATE OR REPLACE FUNCTION update_chunk_search_vector() RETURNS trigger AS $$
            BEGIN
              NEW.search_vector := to_tsvector('english', coalesce(NEW.chunk_text, '') || ' ' || coalesce(NEW.section_title, ''));
              RETURN NEW;
            END
            $$ LANGUAGE plpgsql;

            DROP TRIGGER IF EXISTS trg_update_chunk_search_vector ON banking_document_chunks_hybrid;

            CREATE TRIGGER trg_update_chunk_search_vector
            BEFORE INSERT OR UPDATE ON banking_document_chunks_hybrid
            FOR EACH ROW EXECUTE FUNCTION update_chunk_search_vector();
        """))
        conn.commit()
    print("Stage 10 Hybrid DB schema and triggers initialized successfully.")