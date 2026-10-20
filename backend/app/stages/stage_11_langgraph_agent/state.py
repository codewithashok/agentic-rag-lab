"""
STAGE 11: Agent State Definition
---------------------------------
Defines the shared typed state dictionary across all nodes in the state machine.
"""

from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """
    The central state of the LangGraph agent.
    - messages: uses add_messages reducer so returning a message appends it to the list.
    - loop_count: safeguards against runaway execution.
    - user_id: tenant or account identifier.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    loop_count: int
    user_id: str