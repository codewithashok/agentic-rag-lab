import os
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from openai import OpenAI

# Load variables from .env
load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="Baseline Chat (No RAG)")

# Define request & response schemas using Pydantic
class ChatMessage(BaseModel):
    role: str  # "system", "user", or "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

class ChatResponse(BaseModel):
    reply: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

SYSTEM_PROMPT = {
    "role": "system",
    "content": "You are a professional enterprise software engineering assistant."
}

@app.get("/")
def health_check():
    return {"status": "ok", "message": "Baseline Chat Service Running"}

@app.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest):
    try:
        # Prepend system instruction to the conversation history
        full_conversation = [SYSTEM_PROMPT] + [msg.model_dump() for msg in payload.messages]

        # Call OpenAI Chat Completions API
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=full_conversation,
            temperature=0.2,
        )

        choice = response.choices[0].message.content
        usage = response.usage

        return ChatResponse(
            reply=choice,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            total_tokens=usage.total_tokens,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))