"""
STAGE 10: PostgreSQL Native Hybrid Search + Reranking Router
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException
from openai import OpenAI

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=BACKEND_DIR / ".env")

from app.schemas import ChatRequest, ChatResponse
from app.stages.stage_10_hybrid_pgvector.hybrid_search import (
    execute_postgres_hybrid_search,
    cross_encoder_rerank
)

router = APIRouter(prefix="/stage-10", tags=["Stage 10: Postgres Hybrid + Rerank"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


@router.post("/chat", response_model=ChatResponse)
def stage_10_chat(payload: ChatRequest):
    try:
        user_query = payload.messages[-1].content

        # Step 1: In-Database Hybrid Search (Dense + Sparse with RRF Fusion) -> Top 6 candidates
        candidates = execute_postgres_hybrid_search(
            query_text=user_query,
            tenant_id="retail-business-banking"
        )

        # Step 2: Cross-Encoder Reranker -> Top 2 precision chunks
        top_chunks = cross_encoder_rerank(user_query, candidates, top_k=2)

        context_pieces = []
        for c in top_chunks:
            context_pieces.append(
                f"[Doc: {c['document_name']} | Page: {c['page_number']} | Section: {c['section_title']} | Cross-Score: {c.get('cross_score', 0)}]\n"
                f"{c['chunk_text']}"
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
            stage=f"Stage 10: Postgres Hybrid (HNSW + tsvector) + Rerank (Candidates: {len(candidates)}, Top: {len(top_chunks)})",
            retrieved_context=joined_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))