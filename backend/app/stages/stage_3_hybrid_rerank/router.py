"""
STAGE 3: Hybrid Search (ChromaDB Dense + BM25 Sparse) + Cross-Scoring
---------------------------------------------------------------------
1. Dense Retrieval: ChromaDB (HNSW cosine similarity).
2. Sparse Retrieval: BM25Okapi (Keyword term-frequency matching).
3. Hybrid Fusion: Reciprocal Rank Fusion (RRF) to merge ranks.
4. Reranker / Filtering: Select top candidates for prompt injection.
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Tuple
from fastapi import APIRouter, HTTPException
import chromadb
from openai import OpenAI
from rank_bm25 import BM25Okapi
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/stage-3", tags=["Stage 3: Hybrid Search & Reranking"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Paths and collections
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHROMA_PERSIST_DIR = str(BACKEND_DIR / "chroma_data")
COLLECTION_NAME = "shipping_policy_stage_2"


def tokenize(text: str) -> List[str]:
    """Simple alphanumeric tokenizer for BM25."""
    # It will return all alphanumeric words in lowercase, ignoring punctuation and special characters.
    return re.findall(r"\w+", text.lower())


def get_chroma_collection():
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    return chroma_client.get_collection(name=COLLECTION_NAME)


def dense_search(query: str, top_k: int = 4) -> List[Tuple[str, int]]:
    """Retrieves top_k chunks using ChromaDB embeddings. Returns list of (chunk_text, rank)."""
    collection = get_chroma_collection()

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = response.data[0].embedding

    results = collection.query(query_embeddings=[query_vector], n_results=top_k)
    docs = results.get("documents", [[]])[0]
    return [(doc, rank + 1) for rank, doc in enumerate(docs)]


def sparse_search(query: str, corpus: List[str], top_k: int = 4) -> List[Tuple[str, int]]:
    """Retrieves top_k chunks using BM25 keyword matching. Returns list of (chunk_text, rank)."""
    tokenized_corpus = [tokenize(doc) for doc in corpus]
    bm25 = BM25Okapi(tokenized_corpus)

    tokenized_query = tokenize(query)
    scores = bm25.get_scores(tokenized_query)

    # Rank indices by highest BM25 score
    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:top_k]
    return [(corpus[i], rank + 1) for rank, i in enumerate(ranked_indices) if scores[i] > 0]


def reciprocal_rank_fusion(
    dense_results: List[Tuple[str, int]],
    sparse_results: List[Tuple[str, int]],
    k: int = 60 # score = 1 / (k + rank). Large k keeps ranks close, so chunks found by BOTH searches win.
) -> List[str]:
    """
    Combines dense and sparse search rankings using RRF:
    RRF_Score = SUM(1 / (k + rank))
    """
    rrf_scores: Dict[str, float] = {}

    for doc, rank in dense_results:
        rrf_scores[doc] = rrf_scores.get(doc, 0.0) + (1.0 / (k + rank))

    for doc, rank in sparse_results:
        rrf_scores[doc] = rrf_scores.get(doc, 0.0) + (1.0 / (k + rank))

    # Sort documents by highest combined RRF score
    sorted_docs = sorted(rrf_scores.items(), key=lambda item: item[1], reverse=True)
    return [doc for doc, score in sorted_docs]


def rerank_with_cross_encoder(query: str, candidate_chunks: List[str], top_n: int = 2) -> List[str]:
    """
    Reranker Pass:
    Evaluates candidate chunks against query and returns the top_n most relevant chunks.
    If 2 or fewer candidates exist, returns them directly.
    """
    if len(candidate_chunks) <= top_n:
        return candidate_chunks

    # Use a focused LLM scoring call as a reliable zero-dependency Cross-Encoder
    prompt = (
        "You are a search reranker. Score each candidate chunk's relevance to the query from 0 to 10.\n"
        f"Query: {query}\n\n"
        "Candidates:\n"
    )
    for i, c in enumerate(candidate_chunks):
        # Full chunk: truncating to 200 chars hid answers that sit later in the chunk.
        prompt += f"[{i}] {c}\n\n"
    prompt += "Output ONLY the integer indices of the top 2 best chunks separated by comma (e.g. 0,2):"

    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0
    )

    indices_text = res.choices[0].message.content.strip()
    try:
        selected_indices = [int(idx.strip()) for idx in indices_text.split(",")][:top_n]
        return [candidate_chunks[i] for i in selected_indices if i < len(candidate_chunks)]
    except Exception:
        # Fallback to top candidates from RRF if parsing fails
        return candidate_chunks[:top_n]


@router.post("/chat", response_model=ChatResponse)
def stage_3_chat(payload: ChatRequest):
    try:
        # taking the last user message as the query
        user_query = payload.messages[-1].content

        # 1. Fetch entire corpus from ChromaDB for BM25 indexing
        collection = get_chroma_collection()
        all_docs = collection.get().get("documents", [])

        # 2. Run Dense & Sparse searches
        # retriving related informoation based on the query.
        # dense search ( searching vector embeddings based on the query in vector database)
        dense_hits = dense_search(user_query, top_k=4)
        # sparse search ( searching based on the keywords in the query in the corpus)
        # Here all_docs means, text chunks that are stored in the vector database, which is used for sparse search.
        # not vector embeddings, but the actual text chunks that are stored in the vector database.
        sparse_hits = sparse_search(user_query, all_docs, top_k=4)

        # 3. Fuse rankings via RRF
        fused_candidates = reciprocal_rank_fusion(dense_hits, sparse_hits)

        # 4. Rerank down to top 2 chunks
        best_chunks = rerank_with_cross_encoder(user_query, fused_candidates, top_n=2)
        joined_context = "\n\n---\n\n".join(best_chunks)

        # 5. Grounded prompt generation
        system_instruction = {
            "role": "system",
            "content": (
                "You are an automated support agent for Nexus Retail India.\n"
                "Answer the customer's question strictly using the provided context chunks.\n"
                "If the answer cannot be determined from the context, state what is missing.\n\n"
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
            stage="Stage 3: Hybrid Search & Reranking",
            retrieved_context=joined_context
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))