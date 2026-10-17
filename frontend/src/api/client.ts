import type { ChatRequest, ChatResponse } from './types'

// All calls go through the Vite dev proxy (see vite.config.ts).
const API_BASE = '/api'

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// FastAPI errors come back as { detail: string } (HTTPException)
// or { detail: [{ loc, msg }] } (422 request validation).
function readErrorDetail(body: unknown): string | null {
  if (!body || typeof body !== 'object' || !('detail' in body)) return null
  const { detail } = body as { detail: unknown }
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((d: { loc?: unknown[]; msg?: string }) => `${d.loc?.join('.') ?? ''}: ${d.msg ?? ''}`)
      .join('; ')
  }
  return null
}

async function postJson<TReq, TRes>(path: string, payload: TReq, signal?: AbortSignal): Promise<TRes> {
  let res: Response
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    })
  } catch (err) {
    if (err instanceof DOMException && err.name === 'AbortError') throw err
    throw new ApiError(0, 'Could not reach the backend. Is uvicorn running on port 8000?')
  }

  const text = await res.text()
  let body: unknown = null
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    // Non-JSON body, e.g. the proxy's error page when the backend is down.
  }

  if (!res.ok) {
    const detail = readErrorDetail(body)
    const fallback = res.status >= 500 && !detail ? 'Backend error or backend not running.' : res.statusText
    throw new ApiError(res.status, detail ?? fallback)
  }
  return body as TRes
}

export function sendChat(path: string, request: ChatRequest, signal?: AbortSignal) {
  return postJson<ChatRequest, ChatResponse>(path, request, signal)
}
