"""ai_core/nodes/symptom_refinement_node.py"""

import logging
from typing import Any

from ai_core.chains.symptom_refinement_chain import symptom_refinement_chain
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)


async def symptom_refinement_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Takes the farmer's answer to the investigative question, translates it into
    standard agronomic terminology, and updates the aligned_symptom_profile.
    """
    logger.info("---PROFILE UPDATE NODE---")

    existing_profile = state.get("aligned_symptom_profile", "")
    question = state.get("clarifying_question", "")
    answer = state.get("clarification_answer", "")

    try:
        result = await symptom_refinement_chain.ainvoke({
            "existing_profile": existing_profile,
            "clarifying_question": question,
            "farmer_answer": answer,
        })
        updated_profile = result.updated_symptom_profile
    except Exception:
        logger.exception("Profile update chain failed. Preserving existing profile with raw answer appended.")
        updated_profile = f"{existing_profile} Additional details: {answer}"

    logger.info(f"Updated Symptom Profile: {updated_profile}")

    # Return updated profile and reset question flags before returning to RAG
    return {
        "aligned_symptom_profile": updated_profile,
        "have_question": False,
        "clarifying_question": None,
        "clarification_answer": None,
        "paused_by": None,
    }    