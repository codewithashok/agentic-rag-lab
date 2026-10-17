import { useEffect, useImperativeHandle, useRef, type Ref } from 'react'
import type { ChatStage } from '../api/endpoints'
import { useChat } from '../hooks/useChat'
import { MessageBubble } from './MessageBubble'

export interface ChatPanelHandle {
  send: (text: string) => void
  reset: () => void
}

interface ChatPanelProps {
  endpoint: ChatStage
  ref?: Ref<ChatPanelHandle>
  onLoadingChange?: (id: string, loading: boolean) => void
}

export function ChatPanel({ endpoint, ref, onLoadingChange }: ChatPanelProps) {
  const { messages, loading, error, send, reset } = useChat(endpoint.path)
  const scrollRef = useRef<HTMLDivElement>(null)

  useImperativeHandle(ref, () => ({ send, reset }), [send, reset])

  useEffect(() => {
    onLoadingChange?.(endpoint.id, loading)
  }, [endpoint.id, loading, onLoadingChange])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, loading])

  const threadTokens = messages.reduce((sum, m) => sum + (m.usage?.total_tokens ?? 0), 0)

  return (
    <section className="panel">
      <header className="panel__header">
        <div className="panel__title-row">
          <h2 className="panel__title">
            Stage {endpoint.number} · {endpoint.label}
          </h2>
          <span className="panel__concept">{endpoint.concept}</span>
        </div>
        <code className="panel__route">
          <span className="panel__method">POST</span> /api{endpoint.path}
        </code>
        <p className="panel__description">{endpoint.description}</p>
      </header>

      <div className="panel__messages" ref={scrollRef}>
        {messages.length === 0 && !loading && <p className="panel__empty">Ask a question to call /api{endpoint.path}.</p>}
        {messages.map((m, i) => (
          <MessageBubble key={i} message={m} />
        ))}
        {loading && (
          <div className="message message--assistant">
            <div className="message__bubble message__bubble--loading" aria-label="Waiting for reply">
              <span />
              <span />
              <span />
            </div>
          </div>
        )}
        {error && (
          <div className="panel__error" role="alert">
            {error}
          </div>
        )}
      </div>

      <footer className="panel__footer">
        <span>
          {messages.filter((m) => m.role === 'user').length} turns · {threadTokens} tokens in this thread
        </span>
        <button type="button" className="button-link" onClick={reset} disabled={messages.length === 0 && !error}>
          Clear
        </button>
      </footer>
    </section>
  )
}
