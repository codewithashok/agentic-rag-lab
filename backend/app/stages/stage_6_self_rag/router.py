"""
STAGE 6: Self-Corrective RAG (CRAG)
-----------------------------------
1. Retrieve candidate chunks from ChromaDB.
2. Grade each chunk for relevance using a focused binary classifier.
3. If valid chunks exist -> Generate answer grounded strictly on validated chunks.
4. If no chunks pass the grade -> Trigger hallucination-safe fallback directly.
"""

import os
from pathlib import Path
from typing import List, Tuple
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


def grade_chunk_relevance(query: str, chunk: str):
    """
    Self-RAG Evaluator:
    Checks if a chunk contains relevant facts to address the query.
    Returns (True if relevant else False, token usage of this grading call).
    """
    grader_prompt = (
        "You are a strict document grader assessing relevance for an e-commerce support system.\n"
        "Evaluate whether the retrieved text contains information that directly helps answer the question.\n"
        "Reply with ONLY 'YES' or 'NO'.\n\n"
        f"Question: {query}\n\n"
        f"Retrieved Document:\n{chunk}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": grader_prompt}],
        temperature=0.0,
        max_tokens=5
    )

    verdict = response.choices[0].message.content.strip().upper()
    return "YES" in verdict, response.usage


@router.post("/chat", response_model=ChatResponse)
def stage_6_chat(payload: ChatRequest):
    try:
        user_query = payload.messages[-1].content

        # Step 1: Retrieval
        candidate_chunks = retrieve_raw_chunks(user_query, top_k=3)

        # Step 2: Self-Correction / Grading Step
        valid_chunks = []
        # Grader calls cost tokens too, so count them.
        grading_prompt_tokens = 0
        grading_completion_tokens = 0
        for chunk in candidate_chunks:
            is_relevant, usage = grade_chunk_relevance(user_query, chunk)
            grading_prompt_tokens += usage.prompt_tokens
            grading_completion_tokens += usage.completion_tokens
            if is_relevant:
                valid_chunks.append(chunk)

        # Step 3: Conditional Branching based on Grading
        if not valid_chunks:
            # Fallback path: All chunks failed the relevance test
            return ChatResponse(
                reply=(
                    "I have checked our official shipping and returns documentation, "
                    "but we do not have any policy or rules regarding your specific inquiry. "
                    "Please contact our human support team for further clarification."
                ),
                prompt_tokens=grading_prompt_tokens,
                completion_tokens=grading_completion_tokens,
                total_tokens=grading_prompt_tokens + grading_completion_tokens,
                stage="Stage 6: Self-RAG (Rejected all chunks - Zero Hallucination)",
                retrieved_context="None (All retrieved chunks failed relevance grading)"
            )

        # Generation path: We have verified, graded chunks
        joined_context = "\n\n---\n\n".join(valid_chunks)
        system_instruction = {
            "role": "system",
            "content": (
                "You are an automated support agent for Nexus Retail India.\n"
                "Answer the customer's question strictly using the provided verified context chunks.\n\n"
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
            prompt_tokens=grading_prompt_tokens + response.usage.prompt_tokens,
            completion_tokens=grading_completion_tokens + response.usage.completion_tokens,
            total_tokens=grading_prompt_tokens + grading_completion_tokens + response.usage.total_tokens,
            stage=f"Stage 6: Self-RAG (Retrieved: {len(candidate_chunks)}, Passed Grade: {len(valid_chunks)})",
            retrieved_context=joined_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))