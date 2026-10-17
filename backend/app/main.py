import os
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load environment variables from .env
load_dotenv()

# Import the Stage 0 router
from app.stages.stage_0_baseline.router import router as stage_0_router

app = FastAPI(
    title="Agentic RAG Lab API",
    description="Unified backend server powering progressive stages of RAG development.",
    version="1.0.0"
)

# Enable CORS for frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Stage 0 under the /api prefix -> /api/stage-0/chat
app.include_router(stage_0_router, prefix="/api")

@app.get("/")
def health_check():
    return {
        "status": "online",
        "active_stages": ["/api/stage-0/chat"]
    }