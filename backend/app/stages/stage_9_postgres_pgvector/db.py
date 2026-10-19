"""
STAGE 9: PostgreSQL + pgvector Database Engine
---------------------------------------------
Defines the relational schema with native vector(1536) embeddings,
tenant-isolation metadata, and an HNSW cosine index.
"""

import os
from sqlalchemy import create_engine, Column, Integer, String, Text, Index
from sqlalchemy.orm import declarative_base, sessionmaker
from pgvector.sqlalchemy import Vector

DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://postgres:123456@localhost:5432/agentic_rag_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class DocumentChunk(Base):
    """
    Combines enterprise relational metadata with native vector embeddings.
    """
    __tablename__ = "banking_document_chunks"

    id = Column(Integer, primary_key=True, index=True)
    chunk_id = Column(String(120), unique=True, nullable=False)
    tenant_id = Column(String(50), index=True, nullable=False)  # Multi-tenant isolation
    document_name = Column(String(100), nullable=False)
    page_number = Column(Integer, nullable=False)
    section_title = Column(String(150), nullable=False)
    chunk_text = Column(Text, nullable=False)
    
    # Native pgvector 1536-dimensional vector for text-embedding-3-small
    embedding = Column(Vector(1536), nullable=False)


# HNSW Index for ultra-fast approximate cosine nearest neighbor search
# In SQL: CREATE INDEX ON banking_document_chunks USING hnsw (embedding vector_cosine_ops);
# for example:
# CREATE INDEX idx_document_chunks_embedding_hnsw ON banking_document_chunks USING hnsw (embedding vector_cosine_ops) WITH (m=16, ef_construction=64);
Index(
    "idx_document_chunks_embedding_hnsw",
    DocumentChunk.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"}
)


def init_db():
    """Enables pgvector extension and creates all tables and HNSW indices."""
    with engine.connect() as conn:
        from sqlalchemy import text
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        conn.commit()
    Base.metadata.create_all(bind=engine)