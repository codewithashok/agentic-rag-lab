# Stage 4: Query Transformation & Multi-Query Expansion

## 1. What Broke in Stages 2 & 3?
- **Vocabulary Mismatch Problem:** Users use slang, conversational filler, or indirect phrasing ("guy on his way" vs "Out for Delivery").
- **Compound Queries:** Single queries asking multiple distinct things return an embedding vector that is an average/diluted midpoint of all concepts, missing specific chunks for each.

## 2. Core Techniques
1. **Query Rewriting / Hypothetical Document Embeddings (HyDE):** 
   Rewriting messy conversational inputs into clean, formal statements likely to match indexed enterprise documentation.
2. **Multi-Query Decomposition:** 
   Splitting compound questions into 2-3 independent sub-queries, retrieving chunks for each in parallel, and merging the candidate pool.
3. **Step-Back Prompting:** 
   Generating a higher-level general principle query alongside the specific query to pull broader context.

## 3. Production Trade-offs
- **Latency Cost:** Adds 1 fast LLM call (~300-500ms) before search begins.
- **Cost Trade-off:** We use `gpt-4o-mini` with low max tokens (~50 tokens) for rewriting to keep latency and token costs negligible while multiplying retrieval recall.