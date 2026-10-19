import { useState, type FormEvent, type KeyboardEvent } from 'react'
import { SAMPLE_QUESTIONS } from '../api/endpoints'

interface ComposerProps {
  onSend: (text: string) => void
  busy: boolean
  placeholder?: string
  samples?: string[]
}

export function Composer({
  onSend,
  busy,
  placeholder = 'Ask about shipping, COD, cancellations…',
  samples = SAMPLE_QUESTIONS,
}: ComposerProps) {
  const [text, setText] = useState('')

  const submit = (value: string) => {
    if (!value.trim() || busy) return
    onSend(value)
    setText('')
  }

  const handleSubmit = (e: FormEvent) => {
    e.preventDefault()
    submit(text)
  }

  // Enter sends, Shift+Enter adds a newline.
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey && !e.nativeEvent.isComposing) {
      e.preventDefault()
      submit(text)
    }
  }

  return (
    <div className="composer">
      <div className="composer__samples">
        {samples.map((q) => (
          <button key={q} type="button" className="chip" onClick={() => submit(q)} disabled={busy}>
            {q}
          </button>
        ))}
      </div>
      <form className="composer__form" onSubmit={handleSubmit}>
        <textarea
          className="composer__input"
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={2}
          aria-label="Message"
        />
        <button type="submit" className="button-primary" disabled={busy || !text.trim()}>
          {busy ? 'Waiting…' : 'Send'}
        </button>
      </form>
    </div>
  )
}
