# Agentic RAG Lab — Architect Interview Cheat Sheet (Stages 0 to 7)

A no-nonsense, casual-talk cheat sheet for tech leads, architects, and developers. No textbook fluff—just pure engineering reasoning, trade-offs, and failure modes.

---

## Stage 0: Baseline (No RAG / Pure LLM)

### Q1: Why don't we just prompt the raw model or fine-tune instead of setting up RAG?
**Plain Talk Answer:**  
LLMs only know what was in their public training cut-off. They know zero internal company rules, refund fees, or live database records. If a customer asks about our specific policies, the LLM will not say "I don't know"—it will confidently cook up a believable lie (hallucination).  
Fine-tuning does not fix this either. Fine-tuning teaches a model *how to talk* (style, jargon, tone), not *what live facts to fetch*. For private, constantly changing business data, RAG is the only practical solution.

### Q2: What is the biggest production risk if we ship Stage 0 to real users?
**Plain Talk Answer:**  
Legal and financial liability. A customer asks: *"What is your return fee?"* The raw LLM guesses: *"Returns are 100% free within 30 days"*, but our actual company policy charges an ₹80 return fee. Now customer support is stuck arguing with customers or honoring false promises the model hallucinated.

---

## Stage 1: In-Memory RAG (Full Document Injected in System Prompt)

### Q1: If my document is small (5–10 pages), why do I need a vector DB? Can't I just stuff the whole text into the prompt?
**Plain Talk Answer:**  
You can, and for a tiny document, it actually works great. But two things kill you in production: **cost** and **latency**.  
Every single customer message—even simple greetings like "Hi" or "Thanks"—forces you to pay OpenAI for all 2,000 to 5,000 document tokens repeatedly. Plus, if the document grows from 5 pages to a 200-page banking agreement, it won't fit, or it hits the "Lost in the Middle" problem where the LLM forgets clauses buried halfway down the text.

### Q2: What caused Stage 1 to fail when we asked a multi-part question with one missing rule?
**Plain Talk Answer:**  
The prompt had a strict instruction: *"If the answer cannot be determined from the policy, say: I do not have this information."*  
Because one sub-part of our question wasn't mentioned in the document, a zero-temperature LLM refused to guess and rejected the *entire* question. That showed us how overly rigid negative prompts cause all-or-nothing failures instead of answering what is available and clarifying what is missing.

---

## Stage 2: Vector DB (ChromaDB / Embeddings / HNSW)

### Q1: Explain chunking and overlap like I am a junior developer. Why not store the entire file as one vector?
**Plain Talk Answer:**  
An embedding model squashes text into a fixed list of numbers (a 1,536-dimension vector). If you pass a 10-page document into one vector, the meaning gets diluted like adding 10 liters of water to a single drop of syrup—you can't search for specific details anymore.  
So we slice the document into bite-sized chunks (e.g., 500 characters).  
Why overlap (say 50 characters)? Because if an important sentence gets chopped right in half across Chunk 1 and Chunk 2, both chunks lose the full meaning. Overlap ensures sentences don't get severed without context.

### Q2: What is the biggest blind spot of pure Vector Search (Cosine Similarity / HNSW)?
**Plain Talk Answer:**  
Vector search only understands *concepts*, not *exact characters*.  
If someone searches an exact order ID like `NX-9821`, an error code `ERR_504`, or a specific clause number, vector search fails. It returns chunks that conceptually feel like tracking or errors, but completely misses the exact match. Also, if a question touches three separate sections, a top-2 vector retrieval drops the third section on the floor.

---

## Stage 3: Hybrid Search & Reranking (Dense + Sparse + RRF)

### Q1: Why mix BM25 keyword search with Vector search? What does BM25 add?
**Plain Talk Answer:**  
Think of it like this: Vector search is the guy who understands the *vibe* and *synonyms* (he knows "cost" means "price" or "fee"). BM25 is the strict librarian who matches the *exact spelling* (IDs, numbers, specific codes, product names).  
Running both together gives you the best of both worlds: conceptual meaning from vectors, plus exact keyword hits from BM25.

### Q2: What is RRF (Reciprocal Rank Fusion), and why not just average the vector and BM25 scores?
**Plain Talk Answer:**  
You can't average them because they use completely different scales. Vector cosine similarity runs between 0 and 1, while BM25 scores can be 14.5, 4.2, or 28.3. It's like adding kilometers to kilograms.  
RRF ignores the raw numbers and only looks at their **rank positions** (1st, 2nd, 3rd). It calculates `1 / (60 + rank)` for each list and adds them up. Items that rank near the top across both searches win.

### Q3: What is a Reranker (Cross-Encoder), and why not run it for initial retrieval?
**Plain Talk Answer:**  
Initial vector search (Bi-Encoder) is fast because documents are pre-calculated as vectors and indexed in an HNSW graph. But it compares query and document independently.  
A Reranker (Cross-Encoder) reads the query and candidate chunk *together*, word-by-word, using full cross-attention. It is significantly more accurate, but computationally heavy and slow. The standard pattern is: use fast Hybrid search to grab the top 10 candidates, then let the Reranker pick the top 2 best chunks to pass to the LLM.

---

## Stage 4: Query Transformation & Multi-Query Expansion

### Q1: What problem does Query Transformation solve?
**Plain Talk Answer:**  
The "Garbage In, Garbage Out" problem. Real users don't type clean corporate documentation queries. They type conversational slang like: *"Can I cancel if the delivery guy already left to come here?"*  
Our shipping document doesn't say "delivery guy left". It says "Out for Delivery status".  
Stage 4 places a fast, cheap LLM pass upfront to rewrite messy user slang into 2 or 3 formal, keyword-dense queries before querying the database.

### Q2: Why decompose compound questions?
**Plain Talk Answer:**  
If a user asks: *"What is the Bangalore delivery timeline AND what is the fee if I refuse COD?"*—that is two separate topics sitting in two different sections of the document.  
Embedding that entire sentence into a single vector creates a murky average of both concepts. Query decomposition splits it into two distinct searches, retrieves the right chunks for both, and merges them.

---

## Stage 5: Agentic Routing & Tool Calling

### Q1: In an interview, they ask: "What makes your system an Agent rather than a standard pipeline?" How do you answer?
**Plain Talk Answer:**  
In a pipeline or workflow, **the developer's code** hardcodes what happens next (Step A $\rightarrow$ Step B $\rightarrow$ Step C).  
In an **Agent**, **the LLM controls the steering wheel**.  
We give the LLM a menu of tools (`search_policy`, `track_order`). The LLM reads the user input, decides whether to answer directly, run a vector search, or fetch a live database record, and it can call multiple tools dynamically until it has what it needs. The dynamic decision loop driven by the LLM is what makes it an agent.

### Q2: Does the LLM directly execute SQL or ChromaDB queries?
**Plain Talk Answer:**  
No. The LLM has no hands; it cannot open database sockets or network connections. The LLM simply emits a structured JSON block:  
`"Hey backend, please run track_order with order_id='NX-1001'"`.  
Our Python backend validates that request, securely executes the database query, and feeds the resulting string back into the LLM context so it can format the final answer.

---

## Stage 6: Self-Corrective RAG (CRAG / Evaluator Grader)

### Q1: Why do we need a Grader node? Doesn't the vector DB already return the top matches?
**Plain Talk Answer:**  
A vector database is forced to return top-K matches no matter what. If someone asks: *"Can I pay with Bitcoin?"*, ChromaDB won't say "I don't have this". It will blindly return the closest chunks it has—probably the Cash on Delivery or Prepaid rules.  
If you feed those irrelevant chunks to the LLM, it gets confused and hallucinates. The Grader node acts like a bouncer: it reads the chunks first, says *"None of these have anything to do with Bitcoin"*, tosses them in the trash, and triggers a clean fallback.

### Q2: What is the danger of an overly strict Self-RAG Grader?
**Plain Talk Answer:**  
False rejections. If the grader prompt is too rigid and demands an exact 100% answer to the whole query, it will reject chunks that contain partial or related context. The bot ends up saying *"I don't have this information"* even when the document actually explains the related rule. You must prompt the grader to accept partial and contextual relevance.

---

## Stage 7: LangChain Core & LCEL (LangChain Expression Language)

### Q1: Why use LangChain instead of writing raw Python `openai` client calls?
**Plain Talk Answer:**  
For prototypes, raw OpenAI calls work fine. But in production, you have to write tedious boilerplate: manual string formatting, custom regex to extract JSON, retry loops when the model outputs malformed JSON, and rewriting code if the company switches from OpenAI to Claude or local Ollama.  
LangChain provides:
1. A unified interface across all models.
2. Type-safe prompt templates (`ChatPromptTemplate`).
3. `with_structured_output(PydanticSchema)` which uses native function calling to guarantee valid objects.
4. LCEL (`prompt | llm | parser`), which handles async execution, streaming tokens, and distributed tracing out of the box.

### Q2: What does the Unix pipe `|` in LCEL actually do under the hood?
**Plain Talk Answer:**  
It connects components that implement the `Runnable` protocol. When you write `chain = prompt | llm | parser`:
- `prompt` takes your variables and formats the messages.
- The `|` passes those messages to `llm`.
- `llm` generates the output.
- The next `|` passes that output to `parser`, which validates it against your Pydantic model.  
It also natively supports `.ainvoke()` (async), `.astream()` (streaming tokens), and `.abatch()` (parallel requests) without writing custom concurrency code.