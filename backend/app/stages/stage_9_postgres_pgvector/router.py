"""
STAGE 9: PostgreSQL + pgvector Enterprise RAG Router
----------------------------------------------------
Executes hybrid relational filtering (tenant_id) and 
vector cosine similarity search directly inside local PostgreSQL.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import OpenAI

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

from app.schemas import ChatRequest, ChatResponse
from app.stages.stage_9_postgres_pgvector.db import SessionLocal, DocumentChunk

router = APIRouter(prefix="/stage-9", tags=["Stage 9: PostgreSQL + pgvector RAG"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def search_postgres_pgvector(query: str, tenant_id: str = "retail-business-banking", top_k: int = 2) -> List[DocumentChunk]:
    """
    Executes a combined SQL query:
    1. Relational filter: WHERE tenant_id = :tenant_id
    2. Vector cosine distance: ORDER BY embedding <=> :query_vector
    3. Limit: LIMIT :top_k
    """
    emb_res = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = emb_res.data[0].embedding

    session = SessionLocal()
    try:
        results = (
            session.query(DocumentChunk)
            .filter(DocumentChunk.tenant_id == tenant_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
            .limit(top_k)
            .all()
        )
        return results
    finally:
        session.close()


@router.post("/chat", response_model=ChatResponse)
def stage_9_chat(payload: ChatRequest):
    try:
        user_query = payload.messages[-1].content

        # Retrieve matching chunks from PostgreSQL using pgvector
        matched_chunks = search_postgres_pgvector(user_query, top_k=2)

        context_pieces = []
        for chunk in matched_chunks:
            context_pieces.append(
                f"[Doc: {chunk.document_name} | Page: {chunk.page_number} | Section: {chunk.section_title}]\n"
                f"{chunk.chunk_text}"
            )

        joined_context = "\n\n---\n\n".join(context_pieces)

        system_instruction = {
            "role": "system",
            "content": (
                "You are an enterprise banking support assistant for Nexus Global Bank.\n"
                "Answer the customer's question strictly using the verified context from PostgreSQL.\n"
                "Explain clearly in plain language, and always cite the exact Page Number and Section.\n\n"
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
            stage="Stage 9: PostgreSQL + pgvector (Local HNSW Index)",
            retrieved_context=joined_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))