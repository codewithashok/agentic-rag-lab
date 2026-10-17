import type { ThreadMessage } from '../hooks/useChat'

export function MessageBubble({ message }: { message: ThreadMessage }) {
  const { role, content, usage, latencyMs, retrievedContext } = message

  return (
    <div className={`message message--${role}`}>
      <div className="message__bubble">{content}</div>
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
