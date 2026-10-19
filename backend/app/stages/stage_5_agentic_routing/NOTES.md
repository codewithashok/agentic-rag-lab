# Stage 5: Agentic Routing & Tool Calling (ReAct Loop)

## 1. What Broke in Stages 0 to 4?
- **Unnecessary Retrieval Overhead:** Every query (even "Hi" or "Thanks") triggered vector embeddings and ChromaDB lookups.
- **Static Knowledge Limitation:** RAG can only answer from indexed static documents (`shipping_policy.txt`). It cannot answer dynamic transactional queries (e.g., "Where is my order NX-1002?").

## 2. Core Architectural Concept
- **The LLM as the Dispatcher (Brain):** The LLM evaluates user intent and decides whether to:
  1. Answer directly (chitchat, general help).
  2. Call `search_shipping_policy` (internal static RAG via ChromaDB).
  3. Call `track_order` (live mock transactional DB / Courier API).
- **Tool Calling Protocol (OpenAI Function Calling):**
  - The model does NOT execute code directly.
  - The model outputs a structured JSON `tool_calls` request specifying the function name and arguments.
  - The backend executes the function safely in Python and appends the result as a `tool` role message.
  - The LLM synthesizes the final answer using the retrieved tool output.

## 3. Interview Cheat Sheet (Lead AI Engineer)
- **Q: Does the LLM directly query the database?**
  *A: No. The LLM only emits a structured JSON payload identifying the tool name and validated arguments. The backend runtime inspects the payload, executes the authorized database query or API call, and passes the output back to the LLM context window.*
- **Q: What is the ReAct loop?**
  *A: Reason -> Act -> Observe. The model reasons about what it needs, acts by triggering a tool call, observes the tool output, and either takes another action or returns the final answer.*