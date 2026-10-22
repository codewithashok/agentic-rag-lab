"""
STAGE 15: FastAPI SSE Streaming and Human-in-the-Loop Resumption
"""

import json
import asyncio
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.stages.stage_15_production_api.graph import production_app

router = APIRouter(prefix="/stage-15", tags=["Stage 15: Streaming & Human-in-the-Loop"])


class StreamChatRequest(BaseModel):
    query: str
    thread_id: str


class HumanApprovalRequest(BaseModel):
    thread_id: str
    verdict: str  # "APPROVED" or "REJECTED"


@router.post("/stream")
async def stream_agent_execution(payload: StreamChatRequest):
    """
    Streams step-by-step progress events and tokens via Server-Sent Events (SSE).
    If a compliance hold requires manager review, streams an 'interrupt' event.
    """
    config = {"configurable": {"thread_id": payload.thread_id}}

    async def event_generator():
        initial_state = {
            "messages": [HumanMessage(content=payload.query)],
            "account_number": None,
            "account_data": None,
            "policy_context": None,
            "requires_human_approval": False,
            "human_verdict": None,
            "rejection_reason": None,
            "final_output": None
        }

        yield f"data: {json.dumps({'event': 'status', 'message': 'Initialized agent session'})}\n\n"
        await asyncio.sleep(0.1)

        # Stream node-by-node updates
        for event in production_app.stream(initial_state, config=config, stream_mode="updates"):
            for node_name, state_update in event.items():
                yield f"data: {json.dumps({'event': 'step_completed', 'node': node_name})}\n\n"
                await asyncio.sleep(0.1)

        # Check if the graph was paused at an interrupt
        current_state = production_app.get_state(config)
        if current_state.next and "human_approval_gate" in current_state.next:
            yield f"data: {json.dumps({'event': 'interrupt', 'message': 'PAUSED: Account risk score exceeds 85%. Awaiting Compliance Officer approval.', 'thread_id': payload.thread_id})}\n\n"
            return

        # If completed normally, emit final output
        final_message = current_state.values.get("final_output", "Execution completed.")
        yield f"data: {json.dumps({'event': 'final_reply', 'message': final_message})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.post("/approve")
def approve_pending_action(payload: HumanApprovalRequest):
    """
    Resumes a paused graph execution from its saved checkpoint.
    """
    config = {"configurable": {"thread_id": payload.thread_id}}

    state = production_app.get_state(config)
    if not state.next:
        raise HTTPException(status_code=400, detail="No pending interrupt found for this thread_id.")

    # Update state with human verdict
    production_app.update_state(
        config,
        {"human_verdict": payload.verdict, "requires_human_approval": False},
        as_node="check_ledger_and_policy_node"
    )

    # Resume graph execution to END
    resumed_result = production_app.invoke(None, config=config)

    return {
        "status": "RESUMED_SUCCESSFULLY",
        "thread_id": payload.thread_id,
        "final_reply": resumed_result.get("final_output")
    }