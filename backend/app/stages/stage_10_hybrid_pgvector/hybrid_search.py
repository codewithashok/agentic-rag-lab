"""
STAGE 10: PostgreSQL Hybrid Search & Reranking Engine
"""

import os
from typing import List, Dict, Any
from sqlalchemy import text
from openai import OpenAI
from app.stages.stage_10_hybrid_pgvector.db_schema import SessionLocal

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


def execute_postgres_hybrid_search(
    query_text: str,
    tenant_id: str = "retail-business-banking",
    vector_k: int = 5,
    keyword_k: int = 5,
    rrf_k: int = 60
) -> List[Dict[str, Any]]:
    """
    Executes Dense Vector + Sparse tsvector search directly inside PostgreSQL,
    fusing results using Reciprocal Rank Fusion (RRF).
    """
    # 1. Generate query embedding for dense search
    emb_res = client.embeddings.create(
        model="text-embedding-3-small",
        input=query_text
    )
    query_vector = emb_res.data[0].embedding
    query_vector_str = f"[{','.join(map(str, query_vector))}]"

    session = SessionLocal()
    try:
        # SQL with Common Table Expressions (CTEs) for Dense and Sparse Search
        raw_sql = text(f"""
            WITH dense_results AS (
                SELECT 
                    id, chunk_id, document_name, page_number, section_title, chunk_text,
                    ROW_NUMBER() OVER (ORDER BY embedding <=> :query_vector) AS dense_rank
                FROM banking_document_chunks_hybrid
                WHERE tenant_id = :tenant_id
                LIMIT :vector_k
            ),
            sparse_results AS (
                SELECT 
                    id, chunk_id, document_name, page_number, section_title, chunk_text,
                    ROW_NUMBER() OVER (ORDER BY ts_rank_cd(search_vector, plainto_tsquery('english', :query_text)) DESC) AS sparse_rank
                FROM banking_document_chunks_hybrid
                WHERE tenant_id = :tenant_id
                  AND search_vector @@ plainto_tsquery('english', :query_text)
                LIMIT :keyword_k
            )
            SELECT 
                COALESCE(d.id, s.id) AS id,
                COALESCE(d.chunk_id, s.chunk_id) AS chunk_id,
                COALESCE(d.document_name, s.document_name) AS document_name,
                COALESCE(d.page_number, s.page_number) AS page_number,
                COALESCE(d.section_title, s.section_title) AS section_title,
                COALESCE(d.chunk_text, s.chunk_text) AS chunk_text,
                (COALESCE(1.0 / (:rrf_k + d.dense_rank), 0.0) +
                 COALESCE(1.0 / (:rrf_k + s.sparse_rank), 0.0)) AS rrf_score
            FROM dense_results d
            FULL OUTER JOIN sparse_results s ON d.id = s.id
            ORDER BY rrf_score DESC
            LIMIT 6;
        """)

        results = session.execute(raw_sql, {
            "query_vector": query_vector_str,
            "query_text": query_text,
            "tenant_id": tenant_id,
            "vector_k": vector_k,
            "keyword_k": keyword_k,
            "rrf_k": rrf_k
        }).mappings().all()

        return [dict(row) for row in results]

    finally:
        session.close()


def cross_encoder_rerank(query: str, candidates: List[Dict[str, Any]], top_k: int = 2) -> List[Dict[str, Any]]:
    """
    Reranks the top candidate chunks using a cross-encoder pass to score
    the direct semantic match between the query and each chunk.
    """
    if not candidates:
        return []

    # Fast scoring prompt acting as cross-encoder
    scored_candidates = []
    for c in candidates:
        scoring_prompt = (
            "You are an expert information retrieval cross-encoder.\n"
            "Score the relevance of this banking document chunk to the user question on a scale of 0 to 100.\n"
            "Output ONLY the numeric score, nothing else.\n\n"
            f"Question: {query}\n\n"
            f"Chunk:\n{c['chunk_text']}"
        )
        try:
            res = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": scoring_prompt}],
                temperature=0.0,
                max_tokens=5
            )
            score = float(res.choices[0].message.content.strip())
        except Exception:
            score = 0.0

        c["cross_score"] = score
        scored_candidates.append(c)

    scored_candidates.sort(key=lambda x: x["cross_score"], reverse=True)
    return scored_candidates[:top_k]