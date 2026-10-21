"""
STAGE 14: FastAPI Router for Traced & Evaluated Agent Execution
"""

import uuid
from fastapi import APIRouter, HTTPException

from app.schemas import ChatRequest, ChatResponse
from app.stages.stage_14_observability.tracer import PipelineTracer
from app.stages.stage_14_observability.evaluator import evaluate_rag_turn
from app.stages.stage_13_guardrails.middleware import execute_guarded_agent_pipeline

router = APIRouter(prefix="/stage-14", tags=["Stage 14: Observability & Evaluation"])


@router.post("/chat", response_model=ChatResponse)
def stage_14_chat(payload: ChatRequest):
    try:
        trace_id = f"tr-{uuid.uuid4().hex[:8]}"
        tracer = PipelineTracer(trace_id=trace_id)
        raw_query = payload.messages[-1].content

        # 1. Trace Guardrails & Multi-Agent Execution
        with tracer.span("guarded_multi_agent_pipeline", {"query": raw_query}):
            pipeline_result = execute_guarded_agent_pipeline(raw_query)

        final_reply = pipeline_result["reply"]

        # 2. Trace Evaluation Step
        with tracer.span("ragas_evaluation"):
            mock_context = [
                "Accounts with suspicious transaction match scores above 85% are placed on administrative AML_FREEZE. "
                "The freeze remains until a valid Source of Funds Certificate is submitted and verified."
            ]
            eval_scores = evaluate_rag_turn(
                question=raw_query,
                answer=final_reply,
                contexts=mock_context
            )

        # Consolidate Telemetry
        telemetry = tracer.get_summary()
        
        telemetry_display = (
            f"Trace ID: {telemetry['trace_id']} | Total Time: {telemetry['total_latency_ms']} ms\n"
            f"Spans Recorded: {telemetry['step_count']}\n"
            f"--- Ragas Quality Scores ---\n"
            f"Faithfulness (Grounding): {eval_scores.get('faithfulness', 'N/A')}\n"
            f"Answer Relevance: {eval_scores.get('answer_relevancy', 'N/A')}\n"
            f"--- Audit Trail ---\n"
            f"{pipeline_result.get('audit_trail', 'None')}"
        )

        return ChatResponse(
            reply=final_reply,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            stage=f"Stage 14: Observability & Evaluation ({telemetry['total_latency_ms']}ms)",
            retrieved_context=telemetry_display
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))