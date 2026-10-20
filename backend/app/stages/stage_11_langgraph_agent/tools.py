"""
STAGE 11: Registered Agent Tools
--------------------------------
Tools exposed to the LangGraph agent with strict typing and docstrings.
"""

from langchain_core.tools import tool
from app.stages.stage_10_hybrid_pgvector.hybrid_search import (
    execute_postgres_hybrid_search,
    cross_encoder_rerank
)


@tool
def search_banking_policy(query: str) -> str:
    """
    Search official Nexus Global Bank documentation for rules, fees, wire limits,
    cut-off times, and compliance policies (AML/STR).
    """
    try:
        candidates = execute_postgres_hybrid_search(
            query_text=query,
            tenant_id="retail-business-banking",
            vector_k=4,
            keyword_k=4
        )
        top_chunks = cross_encoder_rerank(query, candidates, top_k=2)
        if not top_chunks:
            return "No verified banking documentation found for this query."

        results = []
        for c in top_chunks:
            results.append(
                f"[Doc: {c['document_name']} | Page: {c['page_number']} | Section: {c['section_title']}]\n{c['chunk_text']}"
            )
        return "\n\n---\n\n".join(results)
    except Exception as e:
        return f"Error searching banking policy database: {str(e)}"


@tool
def fetch_account_balance(account_number: str) -> str:
    """
    Fetch the live balance, currency, and compliance hold status for a specific customer account number.
    """
    # Simulated core banking ledger response
    mock_ledger = {
        "ACC-9901": {
            "status": "AML_FREEZE",
            "balance": 1450000.00,
            "currency": "INR",
            "hold_reason": "Suspicious transaction match score above 85%. Awaiting Source of Funds Certificate."
        },
        "ACC-1002": {
            "status": "ACTIVE",
            "balance": 25000.50,
            "currency": "INR",
            "hold_reason": "None"
        }
    }

    clean_acc = account_number.strip().upper()
    if clean_acc in mock_ledger:
        record = mock_ledger[clean_acc]
        return (
            f"Account {clean_acc}: Status={record['status']}, "
            f"Balance={record['currency']} {record['balance']:,.2f}, "
            f"Hold Reason='{record['hold_reason']}'"
        )
    return f"Account {clean_acc} not found in core ledger."


TOOLS = [search_banking_policy, fetch_account_balance]