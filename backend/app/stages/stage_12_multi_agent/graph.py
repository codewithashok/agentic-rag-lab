"""
STAGE 12: Multi-Agent StateGraph Assembly
-----------------------------------------
Wires Supervisor, Workers, Maker, and Checker with conditional audit loops.
"""

from langgraph.graph import StateGraph, START, END

from app.stages.stage_12_multi_agent.state import MultiAgentState
from app.stages.stage_12_multi_agent.agents import (
    supervisor_node,
    account_specialist_node,
    policy_specialist_node,
    maker_agent_node,
    checker_agent_node
)


# Conditional Router 1: Supervisor routing to specialists or maker
def route_supervisor(state: MultiAgentState) -> str:
    return state.get("next_step", "maker_agent")


# Conditional Router 2: Checker audit decision (Maker-Checker loop)
def route_checker(state: MultiAgentState) -> str:
    """
    If Checker approves -> END
    If Checker rejects -> Loop back to Maker (max 3 retries)
    """
    status = state.get("audit_status", "APPROVED")
    iterations = state.get("iteration_count", 0)

    if status == "APPROVED" or iterations >= 3:
        return END
    
    return "maker_agent"


# Build the Graph
workflow = StateGraph(MultiAgentState)

# 1. Register all specialized nodes
workflow.add_node("supervisor", supervisor_node)
workflow.add_node("account_specialist", account_specialist_node)
workflow.add_node("policy_specialist", policy_specialist_node)
workflow.add_node("maker_agent", maker_agent_node)
workflow.add_node("checker_agent", checker_agent_node)

# 2. Entry point: Always start with the Supervisor
workflow.add_edge(START, "supervisor")

# 3. Supervisor routes conditionally
workflow.add_conditional_edges(
    "supervisor",
    route_supervisor,
    {
        "account_specialist": "account_specialist",
        "policy_specialist": "policy_specialist",
        "maker_agent": "maker_agent"
    }
)

# 4. Specialists route back to supervisor to verify if more data is needed
workflow.add_edge("account_specialist", "supervisor")
workflow.add_edge("policy_specialist", "supervisor")

# 5. Maker generates draft and routes directly to Checker
workflow.add_edge("maker_agent", "checker_agent")

# 6. Checker evaluates draft: either terminates (END) or rejects back to Maker
workflow.add_conditional_edges(
    "checker_agent",
    route_checker,
    {
        END: END,
        "maker_agent": "maker_agent"
    }
)

# Compile the multi-agent system
multi_agent_app = workflow.compile()