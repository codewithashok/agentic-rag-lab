"""
STAGE 15: Resumable Human-in-the-Loop State
------------------------------------------
Carries full conversation context, human review flags, and audit tokens.
"""

from typing import Annotated, Sequence, Optional, Dict, Any
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class ProductionAgentState(TypedDict):
    """Production state supporting streaming events and state persistence."""
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
    account_number: Optional[str]
    account_data: Optional[Dict[str, Any]]
    policy_context: Optional[str]
    
    # Human-in-the-Loop controls
    requires_human_approval: bool
    human_verdict: Optional[str]      # "APPROVED", "REJECTED", or None
    rejection_reason: Optional[str]
    
    final_output: Optional[str]