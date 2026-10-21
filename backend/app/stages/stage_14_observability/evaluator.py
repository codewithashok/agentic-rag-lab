"""
STAGE 14: Automated RAG Triad Evaluator
--------------------------------------
Uses Ragas to run programmatic evaluation on Retrieval Precision,
Faithfulness, and Answer Relevance.
"""

import os
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

eval_llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.0)
eval_embeddings = OpenAIEmbeddings(model="text-embedding-3-small")


def evaluate_rag_turn(
    question: str,
    answer: str,
    contexts: List[str]
) -> Dict[str, Any]:
    """
    Evaluates a single generation turn using Ragas metric primitives.
    Returns scores bounded between 0.0 and 1.0, or None when the evaluator could not run.
    """
    try:
        # Imported lazily: ragas can't be installed alongside openai 3.x (jiter conflict),
        # so a failed import must not stop the whole backend from starting.
        from datasets import Dataset
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy

        # Construct the minimal dataset expected by Ragas
        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts]
        }
        dataset = Dataset.from_dict(data)

        results = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy],
            llm=eval_llm,
            embeddings=eval_embeddings
        )

        return {
            "faithfulness": round(float(results["faithfulness"]), 3),
            "answer_relevancy": round(float(results["answer_relevancy"]), 3)
        }
    except Exception as e:
        # Report "not measured" (None -> JSON null), never a fake score:
        # 1.0 hides hallucinations behind green dashboards, 0.0 corrupts accuracy baselines.
        return {
            "faithfulness": None,
            "answer_relevancy": None,
            "eval_status": "SKIPPED",
            "eval_error": str(e)
        }