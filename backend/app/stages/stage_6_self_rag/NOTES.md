# Stage 6: Self-Corrective RAG (CRAG / Self-RAG)

## 1. What Broke in Earlier Stages?
- **Vector Hallucination & Forced Proximity:** Vector search *always* returns top-K nearest neighbors, even if the cosine distance is huge and the content has zero relevance to the query.
- **Context Pollution:** Passing weakly related chunks confuses the generator model and causes subtle hallucinations or contradictory answers.

## 2. Core Architectural Concept
- **The Evaluator / Document Grader:**
  - Before feeding retrieved documents to the final answer generator, a grading step evaluates document relevance: `(Query, Document) -> 'relevant' | 'irrelevant'`.
  - Irrelevant documents are discarded.
- **Conditional Routing:**
  - If graded chunks are valid: proceed to standard grounded generation.
  - If all chunks fail the grade: bypass generation, preventing hallucination, and return an explicit polite refusal or fallback response.

## 3. Interview Cheat Sheet (Lead AI Engineer)
- **Q: What is the main difference between Reranking (Stage 3) and Document Grading (Stage 6)?**
  *A: Reranking sorts candidates relatively from best to worst. Document Grading evaluates absolute binary relevance (useful vs useless) with a strict threshold, preventing irrelevant chunks from ever entering the final prompt.*
- **Q: What is the latency impact of Self-RAG?**
  *A: It adds a fast grading step (~150-250ms with gpt-4o-mini using binary classification / JSON mode), which protects against expensive hallucination and wrong customer support decisions.*