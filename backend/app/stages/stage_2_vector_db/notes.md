Stage 2: Vector DB (Semantic Retrieval)

1. Ingestion Phase (Offline / One-time)

Read raw document policy text.

Split policy text into small chunks with overlap (e.g., 500 characters, 15% overlap).

Convert each chunk into a vector embedding (text-embedding-3-small, 1536 dimensions).

Save chunks and their embeddings into a Vector Database (ChromaDB HNSW index) on disk.



2. Query Phase (Online / Live Request)

Take question from client.

Convert client's question into a vector embedding using the same embedding model.

Perform semantic vector search in ChromaDB to retrieve only the most relevant snippets (top_k=2).

Augment prompt with only those 2 chunks instead of the entire document.

Ask LLM with the question and the retrieved chunks.

Return answer with lower token usage and faster response time.