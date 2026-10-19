import { useCallback, useRef, useState } from 'react'
import { CHAT_STAGES, STAGES } from './api/endpoints'
import { ChatPanel, type ChatPanelHandle } from './components/ChatPanel'
import { Composer } from './components/Composer'

const COMPARE = 'compare'
// Compare view is hidden for now; flip to true to bring it back.
const SHOW_COMPARE = false

function App() {
  const [page, setPage] = useState<string>(SHOW_COMPARE ? COMPARE : CHAT_STAGES[0].id)
  const [loadingById, setLoadingById] = useState<Record<string, boolean>>({})
  const panels = useRef<Record<string, ChatPanelHandle | null>>({})

  const handleLoadingChange = useCallback((id: string, loading: boolean) => {
    setLoadingById((prev) => (prev[id] === loading ? prev : { ...prev, [id]: loading }))
  }, [])

  const visible = page === COMPARE ? CHAT_STAGES : CHAT_STAGES.filter((s) => s.id === page)
  const busy = visible.some((s) => loadingById[s.id])
  const currentStage = CHAT_STAGES.find((s) => s.id === page)

  // On the Compare page the same message goes to every live stage at once.
  const sendToVisible = (text: string) => {
    visible.forEach((s) => panels.current[s.id]?.send(text))
  }

  return (
    <div className="app">
      <aside className="sidenav">
        <div className="sidenav__brand">
          <h1 className="sidenav__title">Agentic RAG Lab</h1>
          <p className="sidenav__subtitle">Nexus Retail shipping assistant</p>
        </div>
        <nav className="sidenav__list" aria-label="Stages">
          {SHOW_COMPARE && (
            <button
              type="button"
              className={`navitem ${page === COMPARE ? 'navitem--active' : ''}`}
              onClick={() => setPage(COMPARE)}
            >
              <span className="navitem__num">⇆</span>
              <span className="navitem__text">
                <span className="navitem__label">Compare</span>
                <span className="navitem__concept">All live stages side by side</span>
              </span>
            </button>
          )}
          {STAGES.map((s) => {
            const live = Boolean(s.path)
            return (
              <button
                key={s.id}
                type="button"
                className={`navitem ${page === s.id ? 'navitem--active' : ''}`}
                onClick={() => setPage(s.id)}
                disabled={!live}
                title={live ? undefined : 'Not built yet'}
              >
                <span className="navitem__num">{s.number}</span>
                <span className="navitem__text">
                  <span className="navitem__label">{s.label}</span>
                  <span className="navitem__concept">{live ? s.concept : 'Upcoming'}</span>
                </span>
              </button>
            )
          })}
        </nav>
      </aside>

      <div className="workspace">
        {/* Panels stay mounted when switching pages so each thread keeps its history. */}
        <main className={`panels ${page === COMPARE ? 'panels--compare' : ''}`}>
          {CHAT_STAGES.map((s) => (
            <div key={s.id} className="panels__slot" hidden={!visible.includes(s)}>
              <ChatPanel
                endpoint={s}
                ref={(handle) => {
                  panels.current[s.id] = handle
                }}
                onLoadingChange={handleLoadingChange}
              />
            </div>
          ))}
        </main>

        <Composer
          onSend={sendToVisible}
          busy={busy}
          placeholder={page === COMPARE ? 'Send the same question to every stage…' : currentStage?.placeholder}
          samples={currentStage?.samples}
        />
      </div>
    </div>
  )
}

export default App
