import { useCallback, useRef, useState } from 'react'
import { sendChat } from '../api/client'
import type { ChatMessage, TokenUsage } from '../api/types'

export interface ThreadMessage extends ChatMessage {
  usage?: TokenUsage
  latencyMs?: number
  retrievedContext?: string | null
  stage?: string
}

// Holds one conversation thread against one endpoint. The full history is
// sent on every call because the backend is stateless.
export function useChat(path: string) {
  const [messages, setMessages] = useState<ThreadMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  const send = useCallback(
    async (content: string) => {
      const text = content.trim()
      if (!text || loading) return

      const history: ThreadMessage[] = [...messages, { role: 'user', content: text }]
      setMessages(history)
      setLoading(true)
      setError(null)

      const controller = new AbortController()
      abortRef.current = controller
      const started = performance.now()
      try {
        const res = await sendChat(
          path,
          { messages: history.map(({ role, content }) => ({ role, content })) },
          controller.signal,
        )
        setMessages([
          ...history,
          {
            role: 'assistant',
            content: res.reply,
            usage: {
              prompt_tokens: res.prompt_tokens,
              completion_tokens: res.completion_tokens,
              total_tokens: res.total_tokens,
            },
            latencyMs: Math.round(performance.now() - started),
            retrievedContext: res.retrieved_context,
            stage: res.stage,
          },
        ])
      } catch (err) {
        if (err instanceof DOMException && err.name === 'AbortError') return
        setError(err instanceof Error ? err.message : String(err))
      } finally {
        if (abortRef.current === controller) abortRef.current = null
        setLoading(false)
      }
    },
    [path, messages, loading],
  )

  const reset = useCallback(() => {
    abortRef.current?.abort()
    setMessages([])
    setError(null)
    setLoading(false)
  }, [])

  return { messages, loading, error, send, reset }
}
