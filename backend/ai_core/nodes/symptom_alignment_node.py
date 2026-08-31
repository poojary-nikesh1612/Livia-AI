"""ai_core/nodes/symptom_alignment_node.py"""

import logging
from typing import Any

from ai_core.chains.alignment_chain import alignment_chain
from ai_core.constants import SYMPTOM_ALIGNMENT_NODE
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)

# Prevent infinite loops
MAX_RETRIES = 3

def symptom_alignment_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Evaluates whether the user's text and the visual evidence align.
    Manages HITL (Human-In-The-Loop) clarification questions if they don't.
    """
    logger.info("---SYMPTOM ALIGNMENT NODE---")

    user_text = state.get("user_text", "")
    visual_text = state.get("visual_text", "")
    retry_count = state.get("retry_count", 0)
    history_list = state.get("clarification_history", [])

    # Format the clarification history into a clean string 
    if not history_list:
        history_str = "No previous clarification history."
    else:
        history_str = "\n".join(
            f"{'AI' if msg['role'] == 'assistant' else 'Farmer'}: {msg['content']}" 
            for msg in history_list
        )

    # If max retries hit, force the LLM to synthesize the profile
    if retry_count >= MAX_RETRIES:
        logger.warning(f"Alignment retry limit ({retry_count}) reached. Forcing synthesis.")
        history_str += "\n\nSYSTEM OVERRIDE: Maximum clarification attempts reached. You MUST set `is_aligned` to True and synthesize the `aligned_symptom_profile` using the available data. DO NOT ask more questions."

    # Invoke the LCEL chain
    try:
        result = alignment_chain.invoke({
            "user_text": user_text,
            "visual_text": visual_text,
            "history": history_str
        })
    except Exception:
        logger.exception("Alignment LLM failed. Falling back to default alignment.")
        # Fallback to prevent graph crashes if the API times out
        return {
            "retry_count": 0,
            "have_question": False,
            "clarifying_question": None,
            "clarification_answer": None,
            "paused_by": None,
            "aligned_symptom_profile": f"User reported: {user_text}. Visual facts: {visual_text}.",
            "clarification_history": []
        }

    # Handle Mismatch -> Ask Clarifying Question
    if not result.is_aligned and result.clarifying_question and retry_count < 3:
        new_retry = retry_count + 1
        logger.info(f"Mismatch found. Asking question (Attempt {new_retry}): {result.clarifying_question}")
        return {
            "retry_count": new_retry,
            "have_question": True,
            "clarifying_question": result.clarifying_question,
            "clarification_answer": None,  
            "paused_by": SYMPTOM_ALIGNMENT_NODE
        }

    # Handle Perfect Alignment 
    logger.info("Symptoms aligned successfully. Profile generated.")
    
    return {
        "retry_count": 0,                  
        "have_question": False,            
        "clarifying_question": None,       
        "clarification_answer": None,      
        "paused_by": None,                 
        "aligned_symptom_profile": result.aligned_symptom_profile,
        "clarification_history": []        
    }    