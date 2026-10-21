"""
STAGE 12: Multi-Agent Shared State
----------------------------------
Maintains the centralized blackboard state across Supervisor,
Specialized Workers, Maker, and Checker agents.
"""

from typing import Annotated, Sequence, Optional, Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class MultiAgentState(TypedDict):
    """
    Central blackboard state for multi-agent collaboration.
    """
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    # Context artifacts collected by specialists
    account_data: Optional[Dict[str, Any]]
    policy_context: Optional[str]
    
    # Maker-Checker artifacts
    draft_proposal: Optional[str]
    audit_status: Optional[str]        # "APPROVED", "REJECTED", or "PENDING"
    audit_feedback: Optional[str]
    
    # Graph execution controls
    iteration_count: int
    next_step: Optional[str]