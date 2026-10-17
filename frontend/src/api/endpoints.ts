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
  { id: 'stage-2', number: 2, label: 'Vector DB', concept: 'ChromaDB + embeddings', description: 'Top-K chunk retrieval.' },
  { id: 'stage-3', number: 3, label: 'Advanced RAG', concept: 'Hybrid search + rerank', description: 'BM25 + dense + cross-encoder.' },
  { id: 'stage-4', number: 4, label: 'Guardrails', concept: 'Input / output checks', description: 'PII masking, injection defense, RAG triad.' },
  { id: 'stage-5', number: 5, label: 'Tool Agent', concept: 'Function calling', description: 'Dynamic tool routing.' },
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
]
