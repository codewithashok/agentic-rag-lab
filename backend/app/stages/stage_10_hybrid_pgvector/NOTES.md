# Stage 10: PostgreSQL Native Hybrid Search & Cross-Encoder Reranking

## 1. Core Architecture
- **In-Database Dual Retrieval:** Instead of running Python-level BM25 and an external vector DB, PostgreSQL handles both Sparse search (`tsvector` + GIN index) and Dense search (`Vector(1536)` + HNSW index) in one database engine.
- **SQL-Level Reciprocal Rank Fusion (RRF):** PostgreSQL CTEs execute both searches and compute reciprocal rank fusion scores in pure SQL:
  `RRF_Score = 1/(60 + dense_rank) + 1/(60 + sparse_rank)`
- **Cross-Encoder Reranking:** Takes the fused candidate pool (top 6) and applies cross-attention scoring between the query and each chunk to select the top 2 highest-precision contexts.

## 2. Interview Cheat Sheet (Lead AI Architect)
- **Q: Why do Hybrid Search directly inside PostgreSQL rather than in Python?**
  *A: Performance and data locality. In Python, you have to query all vectors, fetch them over the network, query BM25 separately, and merge them in memory. In PostgreSQL, both GIN and HNSW indices run natively in C inside the database engine. You transmit only the fused top-K results over the network wire.*
- **Q: How does `tsvector` handle search differently from `pgvector`?**
  *A: `tsvector` breaks text into normalized lexemes (stems like 'run' from 'running') and matches exact terms, acronyms (STR, FIU, AML), and identifiers. `pgvector` computes geometric cosine angles between semantic concepts. Running both eliminates false negatives for exact codes and acronyms.*