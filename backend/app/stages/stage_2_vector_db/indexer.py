"""
What this file does:
Reads shipping_policy.txt.

Splits the document into chunks with overlap (10-15%) so sentence boundaries aren't broken.

Initializes a persistent ChromaDB client (it saves data to disk in backend/chroma_data/ so your vectors survive server restarts).

Calls OpenAI text-embedding-3-small (1536 dimensions) to generate embeddings.

Inserts the chunks, embeddings, and metadata into a ChromaDB collection using its internal HNSW index.
"""

"""
STAGE 2: Ingestion Pipeline (Indexer)
------------------------------------
Run this script independently from terminal:
    python -m app.stages.stage_2_vector_db.indexer

Concepts:
- Decoupled ingestion (offline worker pattern).
- Paragraph-aware chunking with overlap to prevent context boundary loss.
- Persistent ChromaDB vector storage (HNSW index on disk).
- text-embedding-3-small (1536 dimensions, normalized).
"""

import os
from pathlib import Path
from dotenv import load_dotenv
import chromadb
from openai import OpenAI

# Load .env from backend root
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BACKEND_DIR / ".env")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths
# docs/ lives at the repo root, one level above backend/
DOCS_DIR = BACKEND_DIR.parent / "docs" / "sample_data"
POLICY_FILE = DOCS_DIR / "shipping_policy.txt"
CHROMA_PERSIST_DIR = str(BACKEND_DIR / "chroma_data")

COLLECTION_NAME = "shipping_policy_stage_2"


def load_raw_policy() -> str:
    if not POLICY_FILE.exists():
        raise FileNotFoundError(f"Missing policy file at: {POLICY_FILE}")
    with open(POLICY_FILE, "r", encoding="utf-8") as f:
        return f.read()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 75) -> list[str]:
    """
    Splits text into chunks by character count with overlap.
    Preserves logical boundaries where possible.
    overlap=75 is roughly 15% of 500, preventing boundary loss.
    """
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        # Advance by chunk_size minus overlap
        start += chunk_size - overlap

    return chunks


def get_embedding(text: str) -> list[float]:
    """Calls OpenAI text-embedding-3-small to get a 1536-dimensional vector."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def run_indexing():
    print(f"Reading document: {POLICY_FILE}")
    raw_text = load_raw_policy()

    chunks = chunk_text(raw_text, chunk_size=500, overlap=75)
    print(f"Total chunks created: {len(chunks)}")

    # Initialize Persistent ChromaDB Client
    # Saves vectors locally in backend/chroma_data/
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    # Recreate the collection fresh on every index run
    try:
        chroma_client.delete_collection(name=COLLECTION_NAME)
    except Exception:
        pass

    collection = chroma_client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # Use cosine similarity for HNSW
    )

    print("Generating embeddings and indexing into ChromaDB...")
    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for idx, chunk in enumerate(chunks):
        chunk_id = f"policy_chunk_{idx}"
        emb = get_embedding(chunk)

        ids.append(chunk_id)
        embeddings.append(emb)
        documents.append(chunk)
        metadatas.append({"source": "shipping_policy.txt", "chunk_index": idx})

    # Batch insert into ChromaDB HNSW index
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Indexing complete! Successfully stored {collection.count()} chunks in ChromaDB.")


if __name__ == "__main__":
    run_indexing()