# Stage 14: Observability, Tracing & Production Evaluation

## 1. The RAG Triad Metrics
1. **Context Precision / Recall:** Measures whether the retriever placed the ground-truth information in the top-K chunks.
2. **Faithfulness:** Measures if every claim made in the generated answer can be mathematically grounded in the retrieved chunks (detects hallucination).
3. **Answer Relevance:** Measures whether the generated answer directly addresses the original user prompt without irrelevant verbosity.

## 2. Lead Architect Interview Q&A
- **Q: Why shouldn't you run Ragas evaluation inline on every production user request?**
  *A: Ragas uses LLM-as-a-judge to evaluate faithfulness and relevance, which doubles or triples API latency and token cost. In production, tracing spans are captured inline with lightweight latency, while Ragas evaluation is run asynchronously (via background workers/Celery or sampled across 5-10% of traffic) and on offline regression test sets.*
- **Q: How does distributed tracing differ from application logs?**
  *A: Application logs are disconnected lines of text. Distributed tracing binds every operation across microservices, vector databases, and LLM calls to a single shared `trace_id` with parent-child span hierarchies, capturing exact waterfall latencies and token usage.*