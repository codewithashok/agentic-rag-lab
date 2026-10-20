"""
STAGE 11: FastAPI Router for LangGraph State Machine
"""

from fastapi import APIRouter, HTTPException
from langchain_core.messages import HumanMessage, AIMessage

from app.schemas import ChatRequest, ChatResponse
from app.stages.stage_11_langgraph_agent.graph import banking_agent

router = APIRouter(prefix="/stage-11", tags=["Stage 11: LangGraph State Machine"])


@router.post("/chat", response_model=ChatResponse)
def stage_11_chat(payload: ChatRequest):
    try:
        # Convert frontend messages to LangChain message format
        lc_messages = []
        for msg in payload.messages:
            if msg.role == "user":
                lc_messages.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                lc_messages.append(AIMessage(content=msg.content))

        initial_state = {
            "messages": lc_messages,
            "loop_count": 0,
            "user_id": "customer-session-101"
        }

        # Execute the compiled LangGraph state machine
        final_state = banking_agent.invoke(initial_state)

        # The last message in the graph state is the synthesized reply
        last_message = final_state["messages"][-1]
        
        # Collect intermediate tool traces for observability
        tool_traces = []
        for m in final_state["messages"]:
            if hasattr(m, "tool_calls") and m.tool_calls:
                for tc in m.tool_calls:
                    tool_traces.append(f"Tool Invoked: {tc['name']} with args: {tc['args']}")

        trace_summary = "\n".join(tool_traces) if tool_traces else "Direct generation (no tools used)"

        return ChatResponse(
            reply=last_message.content,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            stage=f"Stage 11: LangGraph Agent (Iterations: {final_state.get('loop_count', 1)})",
            retrieved_context=trace_summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))