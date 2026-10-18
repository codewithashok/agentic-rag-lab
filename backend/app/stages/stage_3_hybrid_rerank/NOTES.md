# Stage 3: Hybrid Search (Dense + Sparse) and Reranking

## 1. The Core Architecture
Stage 3 addresses the fundamental limitations of pure vector search:
- **Vector Search (Dense / HNSW):** Captures conceptual meaning, but struggles with exact codes, PIN codes, clause numbers, and negative constraints.
- **BM25 Search (Sparse / Keyword):** Treats words as exact tokens. Calculates term frequency and inverse document frequency (TF-IDF evolved). Excellent for numbers, IDs, and exact phrases.
- **RRF (Reciprocal Rank Fusion):** Merges rank lists without needing to normalize different scoring scales.
  `Score(d) = 1 / (60 + Rank_dense) + 1 / (60 + Rank_bm25)`
- **Reranker (Cross-Encoder):** Evaluates (Query, Chunk) together via full cross-attention to score true relevance.

## 2. Ingestion vs. Query Lifecycle
- **Ingestion:** Uses existing ChromaDB collection (`shipping_policy_stage_2`) and tokenizes the chunks for the in-memory BM25 index.
- **Query Time:**
  1. Retrieve top-4 chunks from ChromaDB (dense).
  2. Retrieve top-4 chunks from BM25 (sparse).
  3. Combine and deduplicate candidates using RRF.
  4. Rescore candidates with a Cross-Encoder / scoring pass.
  5. Inject top-2 best chunks into `gpt-4o-mini`.

## 3. Interview Cheat Sheet (Lead AI Engineer)
- **Q: Why not use vector search alone?**
  *A: Pure vectors miss exact alphanumeric tokens (order IDs, section numbers, PIN codes) because embeddings project text into conceptual clusters rather than exact character matches.*
- **Q: What is the difference between Bi-Encoder and Cross-Encoder?**
  *A: Bi-encoders (like OpenAI embeddings) encode query and document separately; they are fast for indexing ($O(1)$ lookup via HNSW). Cross-encoders encode query and document together with full cross-attention; they are slower ($O(N)$) but significantly more accurate, making them ideal as a second-stage reranker on a small candidate pool.*
- **Q: What is RRF (Reciprocal Rank Fusion)?**
  *A: A rank aggregation method that combines results from different search algorithms based on ordinal positions rather than raw scores.*