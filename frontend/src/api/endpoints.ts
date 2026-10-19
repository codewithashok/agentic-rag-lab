// One entry per backend stage router. A stage with a `path` that uses the
// ChatRequest -> ChatResponse contract gets a page in the side nav and a Compare
// column; stages without a path are shown as upcoming.

export interface Stage {
  id: string
  number: number
  label: string
  concept: string
  description: string
  path?: string
}

export interface ChatStage extends Stage {
  path: string
}

export const STAGES: Stage[] = [
  {
    id: 'stage-0',
    number: 0,
    label: 'Baseline',
    concept: 'No RAG',
    path: '/stage-0/chat',
    description:
      'GPT-4o with a generic support persona (temperature 0.2). It has never seen the Nexus Retail policy, so expect generic or made-up answers.',
  },
  {
    id: 'stage-1',
    number: 1,
    label: 'In-Memory RAG',
    concept: 'Full document in prompt',
    path: '/stage-1/chat',
    description:
      'The whole shipping_policy.txt is pasted into the system prompt with strict "answer only from the policy" rules (gpt-4o-mini, temperature 0.0). Every question pays for the full document.',
  },
  {
    id: 'stage-2',
    number: 2,
    label: 'Vector DB',
    concept: 'ChromaDB + embeddings',
    path: '/stage-2/chat',
    description:
      'The question is embedded (text-embedding-3-small), ChromaDB returns the top-2 matching policy chunks, and only those go into the prompt (gpt-4o-mini, temperature 0.0). Fewer tokens than Stage 1.',
  },
  {
    id: 'stage-3',
    number: 3,
    label: 'Hybrid + Rerank',
    concept: 'BM25 + vectors + RRF',
    path: '/stage-3/chat',
    description:
      'Two searches run together: ChromaDB (meaning) and BM25 (exact keywords), top-4 each. Reciprocal Rank Fusion merges them, then a gpt-4o-mini reranker picks the best 2 chunks for the prompt.',
  },
  {
    id: 'stage-4',
    number: 4,
    label: 'Query Transform',
    concept: 'Multi-query rewrite',
    path: '/stage-4/chat',
    description:
      'gpt-4o-mini rewrites the question into 2–3 keyword-dense sub-queries (plus the original). Each runs its own vector search (top-2), results are de-duplicated, and all go into the prompt.',
  },
  {
    id: 'stage-5',
    number: 5,
    label: 'Agentic Routing',
    concept: 'Tool calling',
    path: '/stage-5/chat',
    description:
      'gpt-4o-mini decides per question: answer directly, search the policy (vector search), or look up an order (mock DB: NX-1001, NX-1002, NX-1003). It can call both tools in one turn. Tokens include both LLM calls.',
  },
  { id: 'stage-6', number: 6, label: 'LangGraph', concept: 'Stateful agent', description: 'Cyclic graph with human-in-the-loop.' },
  { id: 'stage-7', number: 7, label: 'Multi-Agent', concept: 'Supervisor pattern', description: 'Multiple agents with Redis state.' },
]

export const CHAT_STAGES: ChatStage[] = STAGES.filter((s): s is ChatStage => Boolean(s.path))

// Questions answerable from docs/sample_data/shipping_policy.txt, plus one that isn't.
export const SAMPLE_QUESTIONS = [
  'What is the free delivery threshold?',
  'How much extra does Cash on Delivery cost?',
  'How long does delivery take to Lakshadweep?',
  'Can I cancel my order after it is dispatched?',
  'What happens if delivery fails 3 times on a prepaid order?',
  'Do you offer international shipping?',
  'Where is my order NX-1002 and will I be charged anything?',
  'Hi there!',
]
