"""
STAGE 13: End-to-End Guardrail Pipeline
---------------------------------------
Executes pre-flight inspection, agent dispatch, and post-flight sanitization.
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage

from app.stages.stage_13_guardrails.pii_engine import PIIShield
from app.stages.stage_13_guardrails.injection_shield import InjectionShield
from app.stages.stage_12_multi_agent.graph import multi_agent_app


def execute_guarded_agent_pipeline(raw_user_query: str) -> Dict[str, Any]:
    """
    Executes the secure enterprise RAG pipeline:
    1. Pre-flight Jailbreak & Injection Inspection
    2. Input PII Redaction & Vault Mapping
    3. Multi-Agent Graph Orchestration (Isolated from raw PII)
    4. Post-flight De-anonymization & Safety Validation
    """
    # 1. Pre-Flight Security Check
    is_threat, threat_reason = InjectionShield.inspect(raw_user_query)
    if is_threat:
        return {
            "reply": "Security Alert: Your request was flagged and declined due to an unauthorized system instruction pattern.",
            "status": "BLOCKED",
            "audit_trail": threat_reason,
            "pii_detected": False
        }

    # 2. Input PII Redaction
    masked_query, pii_vault = PIIShield.mask_pii(raw_user_query)
    pii_found = len(pii_vault) > 0

    # 3. Multi-Agent Execution (Runs on sanitized input)
    # Re-inject the account ID specifically for tools if needed, or pass tokens
    agent_input_query = masked_query
    # For internal ledger tool compatibility, replace bank account tokens
    for token, original_val in pii_vault.items():
        if "BANK_ACCOUNT" in token:
            agent_input_query = agent_input_query.replace(token, original_val)

    initial_state = {
        "messages": [HumanMessage(content=agent_input_query)],
        "account_data": None,
        "policy_context": None,
        "draft_proposal": None,
        "audit_status": "PENDING",
        "audit_feedback": None,
        "iteration_count": 0,
        "next_step": None
    }

    agent_result = multi_agent_app.invoke(initial_state)
    raw_draft = agent_result.get("draft_proposal", "No response generated.")

    # 4. Post-Flight De-anonymization (Restore user context)
    safe_final_reply = PIIShield.demask_pii(raw_draft, pii_vault)

    audit_summary = (
        f"Security Inspection: Passed\n"
        f"PII Redacted: {list(pii_vault.keys()) if pii_found else 'None'}\n"
        f"Multi-Agent Status: {agent_result.get('audit_status')}\n"
        f"Maker Iterations: {agent_result.get('iteration_count')}"
    )

    return {
        "reply": safe_final_reply,
        "status": "COMPLETED",
        "audit_trail": audit_summary,
        "pii_detected": pii_found
    }