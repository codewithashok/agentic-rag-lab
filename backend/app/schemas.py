from typing import List, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    """
    Represents a single message in a conversation.
    role: 'system', 'user', or 'assistant'
    content: the text message
    """
    role: str
    content: str

class ChatRequest(BaseModel):
    """
    The incoming payload sent from your client/frontend.
    """
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    """
    The standardized response payload.
    Tracking token metrics from Day 1 lets you see exactly how costs 
    and context sizes change as we move from Stage 0 to Stage N.
    """
    reply: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    stage: str
    retrieved_context: Optional[str] = None