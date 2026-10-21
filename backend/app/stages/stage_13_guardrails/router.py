"""
STAGE 13: FastAPI Router for Guarded Enterprise Agent Execution
"""

from fastapi import APIRouter, HTTPException
from app.schemas import ChatRequest, ChatResponse
from app.stages.stage_13_guardrails.middleware import execute_guarded_agent_pipeline

router = APIRouter(prefix="/stage-13", tags=["Stage 13: Enterprise Guardrails & Safety"])


@router.post("/chat", response_model=ChatResponse)
def stage_13_chat(payload: ChatRequest):
    try:
        raw_query = payload.messages[-1].content
        result = execute_guarded_agent_pipeline(raw_query)

        return ChatResponse(
            reply=result["reply"],
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            stage=f"Stage 13: Guardrails [{result['status']}]",
            retrieved_context=result["audit_trail"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))