"""
STAGE 8: Everyday Business Banking Guide - Section-Aware Search & RAG
--------------------------------------------------------------------
Ingests 'everyday_business_banking_guide.pdf', embeds chunks into ChromaDB,
and returns answers with strict page and section citations.
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException

import chromadb
from openai import OpenAI
from app.schemas import ChatRequest, ChatResponse
from app.stages.stage_8_enterprise_ingestion.ingest_engine import (
    parse_banking_guide_pdf,
    chunk_banking_guide
)

router = APIRouter(prefix="/stage-8", tags=["Stage 8: Everyday Banking PDF Ingestion"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
PDF_PATH = BACKEND_DIR / "docs" / "sample_data" / "everyday_business_banking_guide.pdf"
CHROMA_PERSIST_DIR = str(BACKEND_DIR / "chroma_data")
COLLECTION_NAME = "everyday_banking_guide_stage_8"

# This function initializes ChromaDB and auto-indexes the PDF if the collection is empty.
# converting the PDF into structured chunks with metadata, embedding them, and storing in ChromaDB.
def get_or_create_collection():
    """Initializes ChromaDB and auto-indexes the PDF if the collection is empty."""
    # Initialize ChromaDB client with persistent storage
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)

    try:
        # if the collection already exists and has data, return it
        col = chroma_client.get_collection(name=COLLECTION_NAME)
        if col.count() > 0:
            return col
    except Exception:
        pass

    # If collection doesn't exist or is empty, create it and ingest the PDF
    col = chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    if col.count() == 0:
        if not PDF_PATH.exists():
            raise FileNotFoundError(f"PDF not found at {PDF_PATH}. Please save the file first.")
        # Read the text from PDF file page-by-page and extract raw text with page numbers
        pages = parse_banking_guide_pdf(PDF_PATH)
        # Split the text into clean chunks bounded by numbered section titles and enrich with metadata
        chunks = chunk_banking_guide(pages)

        texts = [c["text"] for c in chunks]
        ids = [c["chunk_id"] for c in chunks]
        metas = [c["metadata"] for c in chunks]

        # Generate embeddings for the chunks using OpenAI's embedding model and store them in ChromaDB
        emb_res = client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        embeddings = [item.embedding for item in emb_res.data]

        col.add(
            ids=ids,
            documents=texts,
            embeddings=embeddings,
            metadatas=metas
        )

    return col


@router.post("/chat", response_model=ChatResponse)
def stage_8_chat(payload: ChatRequest):
    try:
        user_query = payload.messages[-1].content
        collection = get_or_create_collection()

        # Embed user query
        emb_res = client.embeddings.create(
            model="text-embedding-3-small",
            input=user_query
        )
        query_vector = emb_res.data[0].embedding

        # Retrieve top 2 matching chunks
        results = collection.query(
            query_embeddings=[query_vector],
            n_results=2
        )
        # matched_docs and matched_metas are lists of the top 2 retrieved documents and their metadata
        matched_docs = results.get("documents", [[]])[0]
        matched_metas = results.get("metadatas", [[]])[0]

        context_pieces = []
        for doc, meta in zip(matched_docs, matched_metas):
            context_pieces.append(
                f"[Page: {meta['page_number']} | Section: {meta['section_title']}]\n{doc}"
            )

        joined_context = "\n\n---\n\n".join(context_pieces)

        system_instruction = {
            "role": "system",
            "content": (
                "You are a helpful business banking support assistant.\n"
                "Answer the customer's question strictly using the provided context chunks.\n"
                "Explain things in clear, everyday language.\n"
                "Always cite the exact Page Number and Section Title where the answer was found.\n\n"
                f"<verified_context>\n{joined_context}\n</verified_context>"
            )
        }

        full_conversation = [system_instruction] + [
            msg.model_dump() for msg in payload.messages
        ]

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_conversation,
            temperature=0.0
        )

        return ChatResponse(
            reply=response.choices[0].message.content,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            stage="Stage 8: Everyday Banking Guide RAG",
            retrieved_context=joined_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))