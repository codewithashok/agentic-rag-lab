import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env
load_dotenv()

# Import the Stage routers
from app.stages.stage_0_baseline.router import router as stage_0_router
from app.stages.stage_1_in_memory.router import router as stage_1_router
from app.stages.stage_2_vector_db.router import router as stage_2_router
from app.stages.stage_3_hybrid_rerank.router import router as stage_3_router
from app.stages.stage_4_query_transform.router import router as stage_4_router
from app.stages.stage_5_agentic_routing.router import router as stage_5_router
from app.stages.stage_6_self_rag.router import router as stage_6_router

app = FastAPI(
    title="Agentic RAG Lab API",
    description="Unified backend server powering progressive stages of RAG development.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(stage_0_router, prefix="/api")
app.include_router(stage_1_router, prefix="/api")
app.include_router(stage_2_router, prefix="/api")
app.include_router(stage_3_router, prefix="/api")
app.include_router(stage_4_router, prefix="/api")
app.include_router(stage_5_router, prefix="/api")
app.include_router(stage_6_router, prefix="/api")

@app.get("/")
def health_check():
    return {
        "status": "online",
        "active_stages": [
            "/api/stage-0/chat",
            "/api/stage-1/chat",
            "/api/stage-2/chat",
            "/api/stage-3/chat",
            "/api/stage-4/chat",
            "/api/stage-5/chat",
            "/api/stage-6/chat"
        ]
    }