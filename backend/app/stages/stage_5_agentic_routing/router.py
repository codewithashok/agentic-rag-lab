"""
STAGE 5: Agentic Routing & Tool Calling
----------------------------------------
Implements an autonomous agent with two tools:
1. search_shipping_policy: RAG retrieval over ChromaDB.
2. track_order: Mock live database lookup for e-commerce courier tracking.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException
import chromadb
from openai import OpenAI
from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/stage-5", tags=["Stage 5: Agentic Routing"])

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent
CHROMA_PERSIST_DIR = str(BACKEND_DIR / "chroma_data")
COLLECTION_NAME = "shipping_policy_stage_2"

# Mock order database simulating live courier / SQL database
MOCK_ORDERS_DB = {
    "NX-1001": {
        "status": "Out for Delivery",
        "courier": "BlueDart Express",
        "city": "Hyderabad",
        "expected_delivery": "Today by 7:00 PM",
        "payment_mode": "Prepaid"
    },
    "NX-1002": {
        "status": "RTO Initiated (Failed 3 Delivery Attempts)",
        "courier": "Delhivery Logistics",
        "city": "Bengaluru",
        "expected_delivery": "Returning to Origin",
        "payment_mode": "Cash on Delivery",
        "rto_fee_applicable": "INR 80"
    },
    "NX-1003": {
        "status": "In Transit",
        "courier": "Shadowfax",
        "city": "Chennai Hub",
        "expected_delivery": "Within 2 business days",
        "payment_mode": "Prepaid"
    }
}


# --- Tool 1: Vector RAG Search ---
def search_shipping_policy(query: str) -> str:
    """Performs semantic vector search in ChromaDB and returns top-2 relevant chunks."""
    chroma_client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
    collection = chroma_client.get_collection(name=COLLECTION_NAME)

    emb_res = client.embeddings.create(
        model="text-embedding-3-small",
        input=query
    )
    query_vector = emb_res.data[0].embedding

    results = collection.query(
        query_embeddings=[query_vector],
        n_results=2
    )
    docs = results.get("documents", [[]])[0]
    return "\n\n---\n\n".join(docs) if docs else "No relevant shipping policy section found."


# --- Tool 2: Order Database Lookup ---
def track_order(order_id: str) -> str:
    """Fetches real-time order tracking details from the logistics database."""
    clean_id = order_id.strip().upper()
    order_data = MOCK_ORDERS_DB.get(clean_id)
    if not order_data:
        return f"Order ID '{order_id}' was not found in the system. Please verify the ID."
    return json.dumps(order_data, indent=2)


# --- Tool Definitions (Schema for the LLM) ---
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_shipping_policy",
            "description": "Searches the official Nexus Retail India shipping, return, and cancellation policies. Use this whenever the user asks about rules, timelines, fees, damaged shipments, or general policy.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The specific policy topic to search for (e.g. 'Cash on delivery fee', 'RTO policy', 'damaged product reporting window')."
                    }
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "track_order",
            "description": "Retrieves live tracking status, courier partner, and expected delivery date for a specific order ID (e.g. NX-1001, NX-1002).",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The exact order identifier, typically starting with 'NX-'."
                    }
                },
                "required": ["order_id"],
            },
        },
    }
]


@router.post("/chat", response_model=ChatResponse)
def stage_5_chat(payload: ChatRequest):
    try:
        system_prompt = {
            "role": "system",
            "content": (
                "You are an intelligent support agent for Nexus Retail India.\n"
                "You have access to tools:\n"
                "- Use 'search_shipping_policy' to check official guidelines and rules.\n"
                "- Use 'track_order' to look up live customer order details when an order ID is mentioned.\n"
                "- If the user is just saying hello or asking general conversational questions, answer directly without tools.\n"
                "Always be concise, accurate, and professional."
            )
        }

        conversation = [system_prompt] + [
            msg.model_dump() for msg in payload.messages
        ]

        # Step 1: Initial LLM call with tools provided
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0.0
        )

        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls

        # Case A: Model decides NO tools are needed (Direct Conversation)
        if not tool_calls:
            return ChatResponse(
                reply=response_message.content,
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
                stage="Stage 5: Direct Response (Zero Tools)",
                retrieved_context="None (Direct LLM response)"
            )

        # Case B: Model decided to call one or more tools
        conversation.append(response_message)
        executed_contexts = []

        for tool_call in tool_calls:
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "search_shipping_policy":
                tool_output = search_shipping_policy(function_args.get("query", ""))
                executed_contexts.append(f"[Policy Tool Output]:\n{tool_output}")
            elif function_name == "track_order":
                tool_output = track_order(function_args.get("order_id", ""))
                executed_contexts.append(f"[Order DB Output]:\n{tool_output}")
            else:
                tool_output = "Unknown tool requested."

            # Append tool execution result back into conversation
            conversation.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": function_name,
                "content": tool_output
            })

        # Step 2: Final completion where LLM reads the tool output and speaks to the user
        final_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation,
            temperature=0.0
        )

        all_context_str = "\n\n===\n\n".join(executed_contexts)

        return ChatResponse(
            reply=final_response.choices[0].message.content,
            # Two LLM calls (tool choice + final answer), so report both.
            prompt_tokens=response.usage.prompt_tokens + final_response.usage.prompt_tokens,
            completion_tokens=response.usage.completion_tokens + final_response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens + final_response.usage.total_tokens,
            stage=f"Stage 5: Agentic Routing ({', '.join([tc.function.name for tc in tool_calls])})",
            retrieved_context=all_context_str
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))