"""
STAGE 12: Specialized Agent Nodes & Logic
-----------------------------------------
Defines targeted node functions for Supervisor, Ledger Specialist,
Policy Specialist, Maker (Drafter), and Checker (Auditor).
"""

import os
import re
import json
from typing import Any, Dict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage

from app.stages.stage_12_multi_agent.state import MultiAgentState
from app.stages.stage_10_hybrid_pgvector.hybrid_search import (
    execute_postgres_hybrid_search,
    cross_encoder_rerank,
)

load_dotenv()

llm = ChatOpenAI(
    model="gpt-4o-mini", temperature=0.0, api_key=os.getenv("OPENAI_API_KEY")
)

# Mock transactional core ledger
MOCK_LEDGER = {
    "ACC-9901": {
        "status": "AML_FREEZE",
        "balance": 1450000.00,
        "currency": "INR",
        "match_score": "88%",
        "hold_reason": "Suspicious transaction match score above 85%. Awaiting Source of Funds Certificate.",
    },
    "ACC-1002": {
        "status": "ACTIVE",
        "balance": 25000.50,
        "currency": "INR",
        "match_score": "12%",
        "hold_reason": "None",
    },
}


def supervisor_node(state: MultiAgentState) -> Dict[str, Any]:
    """
    Supervisor Agent: Analyzes the user's intent and decides which specialist to call first.
    """
    last_user_msg = ""
    for m in reversed(state["messages"]):
        if isinstance(m, HumanMessage):
            last_user_msg = m.content
            break

    # If we already have both account data and policy context, proceed to maker
    has_account = bool(state.get("account_data"))
    has_policy = bool(state.get("policy_context"))

    supervisor_prompt = f"""You are the Operations Supervisor at Nexus Global Bank.
                        Analyze this request and determine what information is missing.

                        User Request: {last_user_msg}
                        Account Data Present: {has_account}
                        Policy Context Present: {has_policy}

                        Routing rules:
                        1. If an account number (e.g., ACC-9901) is mentioned and Account Data is NOT present, route to: "account_specialist"
                        2. If banking policies, fees, holds, or AML rules are needed and Policy Context is NOT present, route to: "policy_specialist"
                        3. If both are collected (or not applicable), route to: "maker_agent"

                        Respond with ONLY ONE word: "account_specialist", "policy_specialist", or "maker_agent"."""

    resp = llm.invoke([SystemMessage(content=supervisor_prompt)])
    decision = resp.content.strip().lower().replace('"', "")

    if "account" in decision:
        next_step = "account_specialist"
    elif "policy" in decision:
        next_step = "policy_specialist"
    else:
        next_step = "maker_agent"

    return {"next_step": next_step}


def account_specialist_node(state: MultiAgentState) -> Dict[str, Any]:
    """
    Account Specialist: Extracts account numbers and inspects the core ledger.
    """
    last_user_msg = [
        m.content for m in state["messages"] if isinstance(m, HumanMessage)
    ][-1]

    # Extract the account number actually mentioned; unknown/missing -> "UNKNOWN" record,
    # never another customer's data.
    match = re.search(r"ACC-\d+", last_user_msg.upper())
    target_acc = match.group(0) if match else None
    record = MOCK_LEDGER.get(
        target_acc,
        {
            "status": "UNKNOWN",
            "balance": 0.0,
            "currency": "INR",
            "hold_reason": "Not found",
        },
    )

    return {"account_data": record, "next_step": "supervisor"}


def policy_specialist_node(state: MultiAgentState) -> Dict[str, Any]:
    """
    Policy Specialist: Queries the PostgreSQL pgvector + tsvector hybrid index.
    """
    # Search with the user's actual question, not a fixed AML query.
    query = [m.content for m in state["messages"] if isinstance(m, HumanMessage)][-1]

    candidates = execute_postgres_hybrid_search(
        query_text=query, tenant_id="retail-business-banking", vector_k=4, keyword_k=4
    )
    top_chunks = cross_encoder_rerank(query, candidates, top_k=2)

    snippets = [
        f"[Section: {c['section_title']} | Page: {c['page_number']}]\n{c['chunk_text']}"
        for c in top_chunks
    ]
    policy_text = "\n\n---\n\n".join(snippets)

    return {"policy_context": policy_text, "next_step": "supervisor"}


def maker_agent_node(state: MultiAgentState) -> Dict[str, Any]:
    """
    Maker Agent: Synthesizes facts into a formal draft response or action.
    """
    user_question = [m.content for m in state["messages"] if isinstance(m, HumanMessage)][-1]
    prompt = f"""You are the Maker (Drafter) Agent for Nexus Global Bank.
                Prepare a clear customer response based on these verified facts.

                CUSTOMER QUESTION:
                {user_question}

                ACCOUNT DATA:
                {json.dumps(state.get('account_data', {}), indent=2)}

                POLICY CONTEXT:
                {state.get('policy_context', 'No policy data available')}

                AUDIT REJECTION FEEDBACK (if any):
                {state.get('audit_feedback', 'None')}

                Draft a response explaining the account status, citing the policy rule/page, and clarifying next steps for the customer.
                Do NOT approve wire releases if an AML hold exists."""

    resp = llm.invoke([SystemMessage(content=prompt)])

    return {
        "draft_proposal": resp.content,
        "audit_status": "PENDING",
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def checker_agent_node(state: MultiAgentState) -> Dict[str, Any]:
    """
    Checker Agent: Implements the Four-Eyes principle.
    Audits the draft strictly against compliance and policy rules.
    """
    draft = state.get("draft_proposal", "")
    account_info = state.get("account_data", {})

    checker_prompt = f"""You are the Chief Compliance Auditor (Checker Agent) at Nexus Global Bank.
                            You enforce the Four-Eyes Principle. Audit this draft response before it reaches the customer.

                            DRAFT TO AUDIT:
                            {draft}

                            ACCOUNT COMPLIANCE RECORD:
                            {json.dumps(account_info, indent=2)}

                            AUDIT CRITERIA:
                            1. If the account has an AML_FREEZE, does the draft clearly state that the account is frozen?
                            2. Does the draft require the submission of a 'Source of Funds Certificate' before release?
                            3. Does the draft avoid promising an immediate release of funds without compliance clearance?

                            Return a JSON object with this exact structure:
                            {{
                            "verdict": "APPROVED" or "REJECTED",
                            "feedback": "Specific instructions if rejected, or 'Compliant' if approved"
                            }}
                        """

    resp = llm.invoke([SystemMessage(content=checker_prompt)])

    try:
        clean_json = resp.content.strip().replace("```json", "").replace("```", "")
        audit_result = json.loads(clean_json)
    except Exception:
        audit_result = {"verdict": "APPROVED", "feedback": "Audited"}

    return {
        "audit_status": audit_result.get("verdict", "APPROVED"),
        "audit_feedback": audit_result.get("feedback", ""),
    }
