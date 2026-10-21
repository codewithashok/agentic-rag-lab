Architecture & System Foundations (Stages 0 & 1)
What is the fundamental architectural limitation of deploying a pure LLM baseline without external knowledge grounding?

⭐ Why is fine-tuning an LLM an ineffective solution for dynamic enterprise knowledge updates compared to RAG?

How does putting an entire multi-page document into the system prompt impact API token economics and latency at scale?

⭐ What is the "Lost in the Middle" phenomenon in large context windows, and how does it degrade retrieval accuracy?

Why does strict negative prompting in an in-memory RAG setup often cause false-negative refusals on multi-part user queries?

Vector Space, Indexing & Data Structures (Stage 2)
How does dense vector retrieval fundamentally differ from traditional relational keyword searching?

⭐ Why is chunk size optimization necessary instead of embedding an entire multi-page document as a single vector?

What specific retrieval problem does chunk overlap solve at segment boundaries?

⭐ What is an HNSW graph index, and why is it preferred over a flat sequential scan in production vector search?

Under what specific query conditions will pure dense vector search fail to retrieve the correct document chunk?

Hybrid Retrieval & Ranking Mechanics (Stage 3)
Why do enterprise search architectures combine sparse BM25 retrieval with dense vector embeddings?

⭐ What is Reciprocal Rank Fusion, and why can we not simply average the raw scores of BM25 and vector search?

What is the mathematical and structural difference between a Bi-Encoder and a Cross-Encoder?

⭐ Why is it considered an architectural anti-pattern to run a Cross-Encoder directly across an entire vector database?

What are the production trade-offs between hosting a local reranker model versus calling a managed reranking API?

Query Pre-Processing & Latency Management (Stage 4)
What specific retrieval issue does query rewriting solve when handling raw consumer prompts?

How does multi-query expansion improve recall against diverse phrasing in domain documents?

⭐ What is query decomposition, and why must compound user questions be split before retrieval?

⭐ Why is running multi-query expansion unconditionally on every user turn considered a poor engineering design?

How does Hypothetical Document Embeddings compare to multi-query expansion in terms of retrieval alignment and API overhead?

Routing & Tool Execution Patterns (Stage 5)
What is the technical boundary between a deterministic workflow and an agentic workflow?

⭐ How does LLM tool calling work under the hood between the model output and the backend runtime?

Why is the clarity of a tool's semantic description more critical than the internal implementation of the tool's code?

⭐ What architectural safeguards prevent an LLM tool-calling loop from encountering infinite execution cycles?

What is the engineering justification for deploying a bounded two-step tool router instead of an open-ended autonomous loop for consumer RAG?

Retrieval Evaluation & Self-Correction (Stage 6)
What failure mode occurs when a RAG pipeline lacks a pre-generation retrieval grading layer?

⭐ How does document relevance grading differ fundamentally from post-generation hallucination checking?

What fallback strategies should a system execute when retrieved chunks fail the initial relevance threshold?

How do you design grading and evaluation prompts to minimize latency overhead on the user-facing request path?

⭐ What architectural role do state machines play when managing retry loops and query rewrites in Self-RAG systems?

Orchestration & Structured Contracts (Stage 7)
What maintainability problems led the industry to move away from legacy, monolithic LangChain chains?

How does the LangChain Expression Language pipe operator manage data propagation between runnables?

⭐ Why is runtime schema enforcement via Pydantic mandatory for production LLM backend integrations?

What are the technical risks of over-relying on large wrapper libraries rather than core framework primitives?

Enterprise Parsing, Chunking & Ingestion (Stage 8)
⭐ Why do standard character-based text splitters break down when processing enterprise tables and regulatory matrices?

What is section-aware chunking, and how does it preserve document hierarchy and contextual meaning?

⭐ What is the compliance and auditing purpose of metadata enrichment in enterprise document ingestion?

What production tools and models are used to extract multi-column layouts, charts, and scanned diagrams into structured text?

Relational Storage, pgvector & SQL Hybrid Search (Stages 9 & 10)
⭐ What is the dual-write problem in enterprise AI architectures, and how does PostgreSQL with pgvector eliminate it?

How does SQL relational pre-filtering solve tenant isolation and role-based access control during similarity search?

What is the difference between IVFFlat and HNSW indexing strategies inside PostgreSQL?

⭐ What mathematical distance metric does the <=> operator calculate in pgvector?

How does PostgreSQL tsvector tokenization and stemming differ from semantic embedding vectors?

What is the function of a GIN index when executing sparse full-text search in PostgreSQL?

⭐ How do you execute Reciprocal Rank Fusion between dense embeddings and full-text search directly inside a single SQL query?