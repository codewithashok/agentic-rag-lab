"""
STAGE 4: Query Transformation & Multi-Query Expansion
------------------------------------------------------
1. Takes the user's raw, messy question.
2. Uses a fast LLM pass (gpt-4o-mini) to decompose and rewrite it into 
   2-3 concise, domain-specific search queries.
3. Retrieves relevant chunks for all generated sub-queries in parallel.
4. Merges, deduplicates, and provides full coverage context to final LLM.
"""

import os
from pathlib import Path
from typing import List, Set
from fastapi import APIRouter, HTTPException
import chromadb
from openai import OpenAI
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/stage-4", tags=["Stage 4: Query Transformation"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHROMA_PERSIST_DIR = str(BACKEND_DIR / "chroma_data")
COLLECTION_NAME = "shipping_policy_stage_2"


def generate_sub_queries(user_query: str) -> List[str]:
    """
    Decomposes and rewrites messy or compound queries into 2-3 
    clean, targeted search queries tailored for documentation search.
    """
    system_prompt = (
        "You are an expert AI search query optimizer for an Indian e-commerce logistics platform.\n"
        "Your task is to break down the user's input into 2 or 3 distinct, keyword-dense sub-queries "
        "designed to retrieve exact policy clauses from shipping and returns documentation.\n"
        "Rules:\n"
        "- Resolve conversational slang (e.g. 'guy on his way' -> 'out for delivery status').\n"
        "- Return ONLY the queries, one per line. No numbers, no bullet points, no extra text."
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_query}
        ],
        temperature=0.0,
        max_tokens=100
    )

    lines = response.choices[0].message.content.strip().split("\n")
    cleaned_queries = [line.strip().lstrip("1234567890.- ") for line in lines if line.strip()]
    
    # Always include the original query as well to prevent missing anything
    return list(dict.fromkeys([user_query] + cleaned_queries))


def retrieve_chunks_for_queries(queries: List[str], top_k_per_query: int = 2) -> List[str]:
    """Executes vector search for each sub-query and deduplicates retrieved chunks."""
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = chroma_client.get_collection(name=COLLECTION_NAME)

    unique_chunks: Set[str] = set()
    ordered_chunks: List[str] = []

    for q in queries:
        emb_res = client.embeddings.create(
            model="text-embedding-3-small",
            input=q
        )
        query_vector = emb_res.data[0].embedding

        results = collection.query(
            query_embeddings=[query_vector],
            n_results=top_k_per_query
        )
        docs = results.get("documents", [[]])[0]
        for doc in docs:
            if doc not in unique_chunks:
                unique_chunks.add(doc)
                ordered_chunks.append(doc)

    return ordered_chunks


@router.post("/chat", response_model=ChatResponse)
def stage_4_chat(payload: ChatRequest):
    try:
        raw_user_query = payload.messages[-1].content

        # 1. Query Transformation Step
        generated_queries = generate_sub_queries(raw_user_query)

        # 2. Multi-Query Retrieval & Deduplication
        retrieved_chunks = retrieve_chunks_for_queries(generated_queries, top_k_per_query=2)
        joined_context = "\n\n---\n\n".join(retrieved_chunks)

        # 3. Final Grounded Response
        system_instruction = {
            "role": "system",
            "content": (
                "You are an automated support agent for Nexus Retail India.\n"
                "Answer the customer's question thoroughly using the provided context chunks.\n"
                "If certain parts of the question are not covered in the document, state what is missing.\n\n"
                f"<retrieved_context>\n{joined_context}\n</retrieved_context>"
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
            stage=f"Stage 4: Query Transform (Sub-queries: {len(generated_queries)})",
            retrieved_context=joined_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))