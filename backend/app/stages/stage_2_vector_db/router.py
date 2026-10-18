"""
When a user asks a question:

It converts only the question to an embedding.

It queries ChromaDB to fetch only the top-2 most relevant chunks.

It passes only those 2 chunks to gpt-4o-mini.
"""


"""
STAGE 2: Inference Router
-------------------------
FastAPI route handling live queries:
1. Embeds incoming user query.
2. Performs HNSW vector similarity search on ChromaDB.
3. Injects only top-K matching chunks into prompt.
4. Returns grounded answer with token tracking and retrieved context.
"""

import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
import chromadb
from openai import OpenAI
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/stage-2", tags=["Stage 2: Vector DB (ChromaDB)"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Connect to the persistent ChromaDB directory
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHROMA_PERSIST_DIR = str(BACKEND_DIR / "chroma_data")
COLLECTION_NAME = "shipping_policy_stage_2"


def get_query_embedding(query: str) -> list[float]:
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    return response.data[0].embedding


def retrieve_relevant_chunks(query: str, top_k: int = 2) -> list[str]:
    """Queries ChromaDB using HNSW cosine similarity to find top-k chunks."""
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    
    try:
        collection = chroma_client.get_collection(name=COLLECTION_NAME)
    except Exception:
        raise RuntimeError("Chroma collection not found. Did you run indexer.py?")

    query_vector = get_query_embedding(query)

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=top_k
    )

    # results["documents"] is a list of lists: [[chunk_1, chunk_2]]
    documents = results.get("documents", [[]])[0]
    return documents


@router.post("/chat", response_model=ChatResponse)
def stage_2_chat(payload: ChatRequest):
    try:
        # 1. Extract the latest user query from messages
        user_query = payload.messages[-1].content

        # 2. Vector Search: Fetch top-2 relevant chunks only
        matched_chunks = retrieve_relevant_chunks(user_query, top_k=2)
        joined_context = "\n\n---\n\n".join(matched_chunks)

        # 3. Augment Prompt with retrieved chunks only
        system_instruction = {
            "role": "system",
            "content": (
                "You are an automated support agent for Nexus Retail India.\n"
                "Answer the customer's question strictly using the provided context chunks.\n"
                "If the answer cannot be determined from the context, say: "
                "'I do not have this information in the official shipping policy.'\n\n"
                f"<retrieved_context>\n{joined_context}\n</retrieved_context>"
            )
        }

        full_conversation = [system_instruction] + [
            msg.model_dump() for msg in payload.messages
        ]

        # 4. Generate response
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
            stage="Stage 2: Vector DB (ChromaDB)",
            retrieved_context=joined_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))