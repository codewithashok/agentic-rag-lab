// Mirrors the Pydantic schemas in backend/app/schemas.py.

// The backend rejects "system" with 422: the server owns the system prompt.
export type Role = 'user' | 'assistant'

export interface ChatMessage {
  role: Role
  content: string
}

export interface ChatRequest {
  messages: ChatMessage[]
}

export interface ChatResponse {
  reply: string
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  stage: string
  retrieved_context: string | null
}

export type TokenUsage = Pick<ChatResponse, 'prompt_tokens' | 'completion_tokens' | 'total_tokens'>
