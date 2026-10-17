import os
from pathlib import Path
from fastapi import APIRouter, HTTPException
from openai import OpenAI
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/stage-1", tags=["Stage 1: In-Memory RAG"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Resolve path to docs/sample_data/shipping_policy.txt
# parents: [0] stage_1_in_memory, [1] stages, [2] app, [3] backend, [4] repo root (where docs/ lives)
DOCS_DIR = Path(__file__).resolve().parents[4] / "docs" / "sample_data"
POLICY_FILE = DOCS_DIR / "shipping_policy.txt"


def load_shipping_policy() -> str:
    """Reads the raw policy document from disk into server memory."""
    if not POLICY_FILE.exists():
        return "No shipping policy document found."
    # Read the file with UTF-8 encoding to handle special characters
    # Use 'with' to ensure the file is properly closed after reading
    with open(POLICY_FILE, "r", encoding="utf-8") as file:
        return file.read()


@router.post("/chat", response_model=ChatResponse)
def stage_1_chat(payload: ChatRequest):
    try:
        # 1. Retrieval (Simplest form: load the whole document into memory)
        policy_text = load_shipping_policy()

        # 2. Augmentation: Ground the prompt with strict negative constraints
        rag_system_prompt = {
            "role": "system",
            "content": (
                "You are an automated support agent for Nexus Retail India.\n"
                "Answer the customer's question STRICTLY based on the provided shipping policy.\n"
                "If the answer cannot be determined from the policy, say: "
                "'I do not have this information in the official shipping policy.'\n\n"
                f"<policy_document>\n{policy_text}\n</policy_document>"
            ),
        }

        # Build full conversation history
        full_conversation = [rag_system_prompt] + [
            msg.model_dump() for msg in payload.messages
        ]

        # 3. Generation using gpt-4o-mini
        # temperature=0.0 forces deterministic output based strictly on provided facts
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=full_conversation,
            temperature=0.0,
        )

        return ChatResponse(
            reply=response.choices[0].message.content,
            prompt_tokens=response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            stage="Stage 1: In-Memory RAG",
            retrieved_context=policy_text,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
