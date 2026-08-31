"""ai_core/nodes/investigative_question_node.py"""

import logging
from typing import Any

from ai_core.chains.investigative_question_chain import \
    investigative_question_chain
from ai_core.constants import INVESTIGATIVE_QUESTION_NODE
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)

# Prevent infinite loops
MAX_RETRIES = 3

def investigative_question_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Triggered when RAG candidates score below the confidence threshold.
    Analyzes the low-confidence chunks and asks the farmer an open-ended, 
    farmer-friendly question to gather more diagnostic details.
    """
    logger.info("---INVESTIGATIVE QUESTION NODE---")

    profile = state.get("aligned_symptom_profile", "")
    chunks = state.get("retrieved_candidate_chunks", [])
    retry_count = state.get("retry_count", 0)
    
    # Check for Max Retries
    if retry_count >= MAX_RETRIES:
        logger.warning("Max diagnosis retries reached. Forcing fallback.")
        return {
            "have_question": False,
            "retry_count": 0
        }

    # Format the top candidates including their scores
    top_candidates = chunks[:3]
    candidates_text = ""
    for i, chunk in enumerate(top_candidates, 1):
        disease_name = chunk.get("metadata", {}).get("disease_name", f"Candidate {i}")
        score = chunk.get("metadata", {}).get("relevance_score", 0.0)
        content = chunk.get("content", "")
        candidates_text += f"Candidate {i} ({disease_name} - Score: {score:.3f}):\n{content}\n\n"

    logger.info("Invoking LLM for Information Gap Analysis...")

    # Invoke the chain
    try:
        result = investigative_question_chain.invoke({
            "symptom_profile": profile,
            "candidates": candidates_text
        })
        question = result.clarifying_question
    except Exception:
        logger.exception("Investigative Question LLM failed:")
        # Graceful fallback if the LLM crashes
        return {
            "have_question": False,
            "retry_count": 0
        }

    logger.info(f"Generated Investigative Question: {question}")

    # Update the state 
    return {
        "have_question": True,
        "clarifying_question": question,
        "clarification_answer": None, 
        "paused_by": INVESTIGATIVE_QUESTION_NODE,
        "retry_count": retry_count + 1
    }    