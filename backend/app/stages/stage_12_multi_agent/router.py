"""
STAGE 12: FastAPI Router for Multi-Agent Collaboration
"""

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, AIMessage

from app.schemas import ChatRequest, ChatResponse
from app.stages.stage_12_multi_agent.graph import multi_agent_app

router = APIRouter(prefix="/stage-12", tags=["Stage 12: Multi-Agent Collaboration"])


@router.post("/chat", response_model=ChatResponse)
def stage_12_chat(payload: ChatRequest):
    try:
        user_query = payload.messages[-1].content

        initial_state = {
            "messages": [HumanMessage(content=user_query)],
            "account_data": None,
            "policy_context": None,
            "draft_proposal": None,
            "audit_status": "PENDING",
            "audit_feedback": None,
            "iteration_count": 0,
            "next_step": None
        }

        # Execute multi-agent state machine
        final_state = multi_agent_app.invoke(initial_state)

        # The Maker's approved draft proposal is our final response
        final_reply = final_state.get("draft_proposal", "Unable to complete request.")
        
        audit_summary = (
            f"Audit Status: {final_state.get('audit_status')}\n"
            f"Audit Feedback: {final_state.get('audit_feedback')}\n"
            f"Maker Iterations: {final_state.get('iteration_count')}\n"
            f"Account Record Inspected: {bool(final_state.get('account_data'))}\n"
            f"Policy Context Retrieved: {bool(final_state.get('policy_context'))}"
        )

        return ChatResponse(
            reply=final_reply,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            stage="Stage 12: Multi-Agent (Supervisor + Specialists + Maker-Checker Audit)",
            retrieved_context=audit_summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))