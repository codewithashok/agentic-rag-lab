# Agentic RAG Lab — Architect Interview Cheat Sheet (Stages 8 & 9)

A casual, plain-English reference for tech leads, developers, and architects covering enterprise document parsing and SQL vector engines.

---

## Stage 8: Enterprise Document Ingestion & Section Parsing

### Q1: Why can't we use simple character splitters (like chunk_size=500) for enterprise PDFs?
**Plain Talk Answer:**  
Because blind character counters don't understand document structure. If you chop text every 500 characters:
1. **Tables get mangled:** A fee matrix or limit tier turns into a run-on sentence where column names and row values lose alignment.
2. **Orphan clauses:** Sub-clauses (e.g. "Failure to report within 24 hours incurs penalty") get separated from their parent headings, so vector search can't tell what the penalty actually applies to.
Enterprise ingestion requires layout-aware parsing that splits on logical section titles and keeps complete business rules in a single container.

### Q2: What is Metadata Enrichment, and why do auditors care about it?
**Plain Talk Answer:**  
Metadata enrichment means attaching structured tags (`page_number`, `section_title`, `tenant_id`, `document_version`) directly to every text chunk.  
In banking and healthcare, an AI cannot just answer "The fee is INR 500". An auditor will ask: *"Where did that come from, and which legal clause justifies it?"* With metadata attached, the LLM can explicitly cite: *"Page 2, Section 5: What fees might apply"*.

---

## Stage 9: PostgreSQL + pgvector (Relational + Vector Storage)

### Q1: Why are companies replacing standalone vector databases (Pinecone, ChromaDB) with PostgreSQL + pgvector?
**Plain Talk Answer:**  
To kill the **Dual-Write Problem**.  
In any real bank or SaaS, customer records, account tiers, and access permissions already live in PostgreSQL. If vectors live in a separate database (like Pinecone), every document update requires writing to two different places. If one fails or delays, your databases go out of sync.  
With `pgvector`, your relational tables and high-dimensional vectors live in the same ACID-compliant engine. If a transaction rolls back, everything rolls back together.

### Q2: How does metadata pre-filtering work in SQL vector search?
**Plain Talk Answer:**  
In a single SQL query, you can combine standard relational filtering (`WHERE tenant_id = 'org_123'`) with vector distance ranking (`ORDER BY embedding <=> query_vector LIMIT 2`).  
Postgres filters out records that do not match the tenant or user permissions first, and then calculates cosine distance only on authorized rows. You get multi-tenant isolation and similarity search in a single atomic database query.

### Q3: What is the difference between HNSW and IVFFlat in pgvector?
**Plain Talk Answer:**  
- **IVFFlat (Inverted File Flat):** Groups vectors into clusters. It builds faster and consumes less RAM, but search recall drops, and you cannot build it effectively until the table is already loaded with data.
- **HNSW (Hierarchical Navigable Small World):** Builds a multi-layer graph of connected vectors. It takes a bit more memory and build time, but it allows real-time updates and delivers faster queries with much higher accuracy. For production enterprise workloads, HNSW is the standard choice.








Code Walkthrough: Key Lines to Observe in Stage 9Open backend/app/stages/stage_9_postgres_pgvector/ and check these specific lines:1. In db.pyThe Vector Column Definition:Pythonembedding = Column(Vector(1536), nullable=False)
What to observe: We are not storing embeddings as a JSON string, an array of text, or a blob. We are using pgvector.sqlalchemy.Vector(1536).Why: In PostgreSQL, this reserves a fixed-width binary vector representation of 1,536 single-precision floats. This enables low-level SIMD CPU/GPU vector math directly inside the database engine.The HNSW Index Registration:PythonIndex(
    "idx_document_chunks_embedding_hnsw",
    DocumentChunk.embedding,
    postgresql_using="hnsw",
    postgresql_with={"m": 16, "ef_construction": 64},
    postgresql_ops={"embedding": "vector_cosine_ops"}
)
What to observe: Look at postgresql_using="hnsw" and vector_cosine_ops.Why: Without this block, every search is a full sequential table scan ($O(N)$), which slows down as your data grows. With HNSW, PostgreSQL builds a hierarchical multi-layer graph. m=16 sets the number of bidirectional links per node, and ef_construction=64 controls the search breadth during build time. At query time, the search traverses the graph in $O(\log N)$ time, yielding sub-millisecond retrieval.The Extension Bootstrap:Pythonconn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
What to observe: This raw SQL executes before any SQLAlchemy tables are declared.Why: If the vector extension is not enabled in PostgreSQL first, any CREATE TABLE containing a Vector type will fail with a syntax error (type "vector" does not exist).2. In router.pyThe Atomic Relational + Vector Filter:Pythonresults = (
    session.query(DocumentChunk)
    .filter(DocumentChunk.tenant_id == tenant_id)
    .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
    .limit(top_k)
    .all()
)
What to observe: Look at .cosine_distance(query_vector).Why: In raw SQL, SQLAlchemy translates this into the PostgreSQL <=> operator:SQLSELECT * FROM banking_document_chunks 
WHERE tenant_id = 'retail-business-banking'
ORDER BY embedding <=> '[0.012, -0.043, ...]' 
LIMIT 2;
Why this matters for architects: This is pre-filtering in a single query. In standalone vector databases, you either retrieve top-K vectors first and filter out unauthorized tenants in Python (which drops your result count below $K$), or you maintain separate vector indexes per tenant. In PostgreSQL, relational permissions and vector proximity happen in a single execution plan.3. In indexer.pyChecking Existing Records Before Indexing:Pythoncount = session.query(DocumentChunk).count()
if count > 0:
    print("Database already contains chunks. Skipping...")
    return
What to observe: We verify table state before generating vectors.Why: In production ETL pipelines, failing to check table state leads to duplicate vectors, inflated storage costs, and duplicate context chunks returned to the prompt.Whenever you are ready, let me know and we will advance to Stage 10: PostgreSQL Full-Text Search (tsvector) + pgvector Hybrid Search & Cross-Encoder Reranking, with this same line-by-line breakdown at the end!