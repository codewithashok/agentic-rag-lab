"""
STAGE 11: LangGraph Workflow Compilation
----------------------------------------
Builds the StateGraph, binds tools, handles routing, and compiles the executable graph.
"""

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.stages.stage_11_langgraph_agent.state import AgentState
from app.stages.stage_11_langgraph_agent.tools import TOOLS

load_dotenv()

SYSTEM_PROMPT = """You are a senior banking AI assistant for Nexus Global Bank.
You have access to tools:
1. 'search_banking_policy': Look up official banking guides, rules, limits, and fees.
2. 'fetch_account_balance': Check live account balances and account hold statuses.

Always explain your answers clearly and cite the exact document section or account status provided by your tools.
If you have retrieved all necessary facts, synthesize the final answer directly without calling further tools."""

# 1. Initialize LLM and bind available tools
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=os.getenv("OPENAI_API_KEY")
)
llm_with_tools = llm.bind_tools(TOOLS)


# 2. Node: The LLM decision agent
def agent_node(state: AgentState):
    """Invokes the model with conversation history and system instructions."""
    messages = state["messages"]
    
    # Prepend system message if not already present
    if not isinstance(messages[0], SystemMessage):
        messages = [SystemMessage(content=SYSTEM_PROMPT)] + list(messages)

    # Invoke the LLM with tools and return the updated state
    response = llm_with_tools.invoke(messages)
    
    current_loops = state.get("loop_count", 0) + 1
    return {
        "messages": [response],
        "loop_count": current_loops
    }


# 3. Conditional Router: Decides whether to continue looping or stop
def should_continue(state: AgentState):
    """
    Inspects the last message. If the LLM requested a tool, route to 'tools_node'.
    Otherwise, route to END. Safeguards against runaway loops (> 5 iterations).
    """
    messages = state["messages"]
    last_message = messages[-1]

    # Infinite loop guardrail
    if state.get("loop_count", 0) >= 5:
        return END

    # If the LLM generated tool calls, route to tools
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools_node"

    return END


# 4. Node: Tool Executor
tools_node = ToolNode(TOOLS)


# 5. Assemble the Graph
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("agent_node", agent_node)
workflow.add_node("tools_node", tools_node)

# Add edges
workflow.add_edge(START, "agent_node")

# Conditional edge out of agent_node
workflow.add_conditional_edges(
    "agent_node",
    should_continue,
    {
        "tools_node": "tools_node",
        END: END
    }
)

# Loop edge: After executing tools, always route back to the agent
workflow.add_edge("tools_node", "agent_node")

# Compile graph into an executable runnable
banking_agent = workflow.compile()