"""
STAGE 7: LangChain Core Primitives & LCEL (LangChain Expression Language)
--------------------------------------------------------------------------
Demonstrates enterprise-grade structured output, prompt templating,
and runnable composition using LangChain's modern LCEL architecture.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, HTTPException

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.schemas import ChatRequest, ChatResponse

router = APIRouter(prefix="/stage-7", tags=["Stage 7: LangChain Core & LCEL"])

# 1. Unified Model Abstraction
llm = ChatOpenAI(
    model="gpt-4o-mini",
    temperature=0.0,
    api_key=os.getenv("OPENAI_API_KEY")
)


# 2. Strict Pydantic Schema for Guaranteed Structured Output
class PolicyComplianceAssessment(BaseModel):
    query_topic: str = Field(
        description="The primary domain of the user's inquiry (e.g. 'Shipping SLA', 'Fees', 'Damage Claim', 'Cancellation')."
    )
    is_actionable: bool = Field(
        description="True if the inquiry can be resolved with existing documented policies; False if out of scope or invalid."
    )
    risk_level: str = Field(
        description="Risk level: 'LOW' for informational queries, 'MEDIUM' for disputes/damage, 'HIGH' for legal/fraud claims."
    )
    customer_response: str = Field(
        description="The clear, grounded, professional response addressing the customer's inquiry."
    )
    suggested_followups: List[str] = Field(
        default_factory=list,
        description="2-3 relevant follow-up actions or questions the customer might need."
    )


# 3. Type-Safe Prompt Template
compliance_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an enterprise logistics compliance and support engine for Nexus Retail India.\n"
        "Evaluate the customer's inquiry and provide a structured compliance assessment.\n"
        "Always be precise, grounded, and courteous."
    ),
    ("human", "{user_inquiry}")
])


# 4. Build Structured LCEL Chain
# Prompt -> LLM (bound to Pydantic Schema) -> Validated Pydantic Instance
structured_chain = compliance_prompt | llm.with_structured_output(PolicyComplianceAssessment)


@router.post("/chat", response_model=ChatResponse)
async def stage_7_chat(payload: ChatRequest):
    try:
        user_query = payload.messages[-1].content

        # Execute the LCEL chain asynchronously
        assessment: PolicyComplianceAssessment = await structured_chain.ainvoke({
            "user_inquiry": user_query
        })

        formatted_reply = (
            f"**Assessment Topic:** {assessment.query_topic} (Risk: {assessment.risk_level})\n\n"
            f"{assessment.customer_response}\n\n"
            f"**Suggested Next Steps:**\n" +
            "\n".join([f"- {item}" for item in assessment.suggested_followups])
        )

        context_summary = (
            f"Actionable: {assessment.is_actionable} | "
            f"Risk: {assessment.risk_level} | "
            f"Topic: {assessment.query_topic}"
        )

        return ChatResponse(
            reply=formatted_reply,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
            stage="Stage 7: LangChain Core & LCEL Structured Output",
            retrieved_context=context_summary
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))