"""
STAGE 6: Self-Corrective RAG (CRAG)
-----------------------------------
1. Retrieve candidate chunks from ChromaDB.
2. Grade candidate chunks for relevance using a balanced evaluator.
3. If valid chunks exist -> Generate answer grounded strictly on verified chunks.
4. If no chunks pass the grade -> Trigger hallucination-safe fallback directly.
"""

import os
from pathlib import Path
from typing import List
from fastapi import APIRouter, HTTPException
import chromadb
from openai import OpenAI
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/stage-6", tags=["Stage 6: Self-Corrective RAG"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHROMA_PERSIST_DIR = str(BACKEND_DIR / "chroma_data")
COLLECTION_NAME = "shipping_policy_stage_2"


def retrieve_raw_chunks(query: str, top_k: int = 3) -> List[str]:
    """Retrieves top-k candidate chunks from ChromaDB."""
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = chroma_client.get_collection(name=COLLECTION_NAME)

    emb_res = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = emb_res.data[0].embedding

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )
    return results.get("documents", [[]])[0]


def grade_chunk_relevance(query: str, chunk: str) -> bool:
    """
    Self-RAG Evaluator:
    Checks if a chunk is semantically relevant or provides contextual facts
    (e.g., returns, claims, transit damage, RTO, cancellations, fees).
    """
    grader_prompt = (
        "You are an intelligent document relevance evaluator for an e-commerce support system.\n"
        "Determine if the retrieved text contains ANY useful facts, policies, or context "
        "related to the customer's inquiry (such as returns, damaged goods, RTO, cancellations, or fees).\n"
        "If it provides ANY related context that helps clarify what is or isn't allowed, output 'YES'.\n"
        "If the document is completely unrelated, output 'NO'.\n\n"
        f"User Query: {query}\n\n"
        f"Retrieved Chunk:\n{chunk}\n\n"
        "Decision (YES/NO):"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": grader_prompt}],
        temperature=0.0,
        max_tokens=5
    )

    verdict = response.choices[0].message.content.strip().upper()
    return "YES" in verdict


@router.post("/chat", response_model=ChatResponse)
def stage_6_chat(payload: ChatRequest):
    try:
        user_query = payload.messages[-1].content

        # Step 1: Retrieval
        candidate_chunks = retrieve_raw_chunks(user_query, top_k=3)

        # Step 2: Self-Correction / Grading Step
        valid_chunks = []
        for chunk in candidate_chunks:
            if grade_chunk_relevance(user_query, chunk):
                valid_chunks.append(chunk)

        # Step 3: Conditional Branching based on Grading
        if not valid_chunks:
            return ChatResponse(
                reply=(
                    "I have checked our official shipping and returns documentation, "
                    "but we do not have any policy or rules regarding your specific inquiry. "
                    "Please contact our human support team for further clarification."
                ),
                prompt_tokens=0,
                completion_tokens=0,
                total_tokens=0,
                stage="Stage 6: Self-RAG (Rejected all chunks - Zero Hallucination)",
                retrieved_context="None (All retrieved chunks failed relevance grading)"
            )

        # Step 4: Grounded Generation with verified chunks
        joined_context = "\n\n---\n\n".join(valid_chunks)
        system_instruction = {
            "role": "system",
            "content": (
                "You are an automated support agent for Nexus Retail India.\n"
                "Answer the customer's question strictly using the provided verified context chunks.\n"
                "If certain parts of the question are not covered in the document, state what is missing.\n\n"
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
            stage=f"Stage 6: Self-RAG (Retrieved: {len(candidate_chunks)}, Passed Grade: {len(valid_chunks)})",
            retrieved_context=joined_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))