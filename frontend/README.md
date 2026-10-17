# Frontend

React + TypeScript + Vite playground for the stage routers in `../backend/app`.

## Run

```bash
# terminal 1 – backend
cd backend
venv\Scripts\activate
uvicorn app.main:app --reload    # http://127.0.0.1:8000

# terminal 2 – frontend
cd frontend
npm install
npm run dev                      # http://localhost:5173
```

The Vite dev server forwards `/api/*` to the backend unchanged.
To point at a different backend, create `frontend/.env.local` with `BACKEND_URL=http://host:port`.

## Pages

| Side nav | Route | What it shows |
|---|---|---|
| Compare | all live stages | Same question sent to every stage side by side |
| Stage 0 · Baseline | `POST /api/stage-0/chat` | GPT-4o with no policy context |
| Stage 1 · In-Memory RAG | `POST /api/stage-1/chat` | Whole policy injected into the prompt |
| Stages 2–7 | – | Listed as upcoming |

Each reply shows prompt / completion / total tokens, latency, and the `retrieved_context` the backend returned.

## Adding a stage

- Same `ChatRequest -> ChatResponse` shape: give the stage a `path` in `src/api/endpoints.ts`. It becomes clickable in the side nav and joins Compare.
- New shape: add its types to `src/api/types.ts` and a function to `src/api/client.ts`, then build a view for it.
