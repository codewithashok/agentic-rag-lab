import type { ReactNode } from 'react'
import type { ThreadMessage } from '../hooks/useChat'

// Renders **bold** spans from markdown replies; everything else stays plain text.
function renderBold(text: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) =>
    part.startsWith('**') && part.endsWith('**') ? <strong key={i}>{part.slice(2, -2)}</strong> : part,
  )
}

export function MessageBubble({ message }: { message: ThreadMessage }) {
  const { role, content, usage, latencyMs, retrievedContext, stage } = message

  return (
    <div className={`message message--${role}`}>
      {/* The backend's own label for how it answered, e.g. which tools an agent called. */}
      {stage && <div className="message__stage">{stage.replace(/^Stage \d+:\s*/, '')}</div>}
      <div className="message__bubble">{renderBold(content)}</div>
      {usage && (
        <div className="message__meta" title="Prompt tokens include the system prompt, any injected context and the whole history.">
          <span>prompt {usage.prompt_tokens}</span>
          <span>completion {usage.completion_tokens}</span>
          <span className="message__meta-total">total {usage.total_tokens}</span>
          {latencyMs !== undefined && <span>{(latencyMs / 1000).toFixed(1)}s</span>}
        </div>
      )}
      {retrievedContext && (
        <details className="message__context">
          <summary>Retrieved context · {retrievedContext.length.toLocaleString()} chars</summary>
          <pre>{retrievedContext}</pre>
        </details>
      )}
    </div>
  )
}
