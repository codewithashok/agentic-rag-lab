"""
STAGE 15: Stateful Graph with Human-in-the-Loop Interrupts
---------------------------------------------------------
Configures checkpointed execution using thread_id sessions and
supports programmatic graph interruptions for manager authorizations.
"""

import os
from typing import Any, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.stages.stage_15_production_api.state import ProductionAgentState
from app.stages.stage_10_hybrid_pgvector.hybrid_search import (
    execute_postgres_hybrid_search,
    cross_encoder_rerank
)

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    streaming=True,  # Mandatory for token streaming
    api_key=os.getenv("OPENAI_API_KEY")
)

# In-memory checkpointer (for enterprise clustering, replace with PostgresSaver)
checkpointer = MemorySaver()


def intake_node(state: ProductionAgentState) -> Dict[str, Any]:
    """Inspects query and extracts account targets."""
    last_msg = state["messages"][-1].content
    account_target = "ACC-9901" if "9901" in last_msg else "ACC-1002"
    return {"account_number": account_target}


def check_ledger_and_policy_node(state: ProductionAgentState) -> Dict[str, Any]:
    """Fetches core banking status and grounds in compliance policy."""
    acc = state.get("account_number", "ACC-9901")
    
    # Ledger mock
    is_high_risk = (acc == "ACC-9901")
    record = {
        "status": "AML_FREEZE" if is_high_risk else "ACTIVE",
        "balance": 1450000.00 if is_high_risk else 25000.50,
        "risk_score": 88 if is_high_risk else 12,
        "hold_reason": "Suspicious transaction match score above 85%."
    }

    # Policy RAG
    candidates = execute_postgres_hybrid_search(
        query_text="AML freeze Source of Funds Certificate",
        tenant_id="retail-business-banking",
        vector_k=3,
        keyword_k=3
    )
    top_chunks = cross_encoder_rerank("AML freeze Source of Funds Certificate", candidates, top_k=1)
    policy_doc = top_chunks[0]["chunk_text"] if top_chunks else "Policy Section 6: AML Restrictions apply."

    return {
        "account_data": record,
        "policy_context": policy_doc,
        # Triggers interrupt if risk score > 85
        "requires_human_approval": is_high_risk and (state.get("human_verdict") is None)
    }


def human_approval_gate(state: ProductionAgentState) -> Dict[str, Any]:
    """
    Simulated human compliance action.
    This node only executes after a manager submits an approval.
    """
    verdict = state.get("human_verdict", "APPROVED")
    return {
        "requires_human_approval": False,
        "rejection_reason": None if verdict == "APPROVED" else "Manager rejected freeze override."
    }


def synthesis_node(state: ProductionAgentState) -> Dict[str, Any]:
    """Synthesizes customer explanation based on approved facts."""
    acc = state.get("account_data", {})
    policy = state.get("policy_context", "")
    human_status = state.get("human_verdict")

    prompt = f"""You are a senior banking advisor at Nexus Global Bank.
Customer Inquiry: {state['messages'][0].content}
Account State: {acc}
Policy Context: {policy}
Human Compliance Officer Decision: {human_status or 'Standard Automated Flow'}

Provide a professional, clear response explaining why the account is restricted,
what documents (Source of Funds Certificate) are required, and the manager's review status."""

    response = llm.invoke([SystemMessage(content=prompt)])
    return {
        "messages": [response],
        "final_output": response.content
    }


# Routing logic
def route_approval_check(state: ProductionAgentState) -> str:
    if state.get("requires_human_approval"):
        return "human_approval_gate"
    return "synthesis_node"


# Graph Construction
workflow = StateGraph(ProductionAgentState)

workflow.add_node("intake_node", intake_node)
workflow.add_node("check_ledger_and_policy_node", check_ledger_and_policy_node)
workflow.add_node("human_approval_gate", human_approval_gate)
workflow.add_node("synthesis_node", synthesis_node)

workflow.add_edge(START, "intake_node")
workflow.add_edge("intake_node", "check_ledger_and_policy_node")

workflow.add_conditional_edges(
    "check_ledger_and_policy_node",
    route_approval_check,
    {
        "human_approval_gate": "human_approval_gate",
        "synthesis_node": "synthesis_node"
    }
)

workflow.add_edge("human_approval_gate", "synthesis_node")
workflow.add_edge("synthesis_node", END)

# COMPILE WITH:
# 1. checkpointer to preserve conversation thread state
# 2. interrupt_before to halt execution before human_approval_gate runs
production_app = workflow.compile(
    checkpointer=checkpointer,
    interrupt_before=["human_approval_gate"]
)