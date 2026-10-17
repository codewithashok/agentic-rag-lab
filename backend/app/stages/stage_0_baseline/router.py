import os
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from app.schemas import ChatRequest, ChatResponse

# Prefix every endpoint in this router with /stage-0
router = APIRouter(prefix="/stage-0", tags=["Stage 0: Baseline - (No RAG)"])

# Initialize OpenAI client (reads OPENAI_API_KEY from environment)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a customer support assistant for an Indian e-commerce platform."
}

@router.post("/chat", response_model=ChatResponse)
def stage_0_chat(payload: ChatRequest):
    try:
        # Construct the full conversation: [System Instruction, ...User Messages]
        conversation = [SYSTEM_PROMPT] + [msg.model_dump() for msg in payload.messages]
        # Call OpenAI Chat Completions API
        response = client.chat.completions.create(
            model="gpt-4o-mini",   # <-- Use the lightweight, cost-effective model
            messages=conversation,
            temperature=0.2,
        )

        return ChatResponse(
            reply=response.choices[0].message.content,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            stage="Stage 0: Baseline (No RAG)",
            retrieved_context=None
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))