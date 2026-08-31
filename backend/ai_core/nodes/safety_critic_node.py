"""ai_core/nodes/safety_critic_node.py"""

import logging
from typing import Any

from ai_core.chains.safety_critic_chain import safety_critic_chain
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)

# Prevent infinite loops
MAX_RETRIES = 3

async def safety_critic_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Evaluates the generated diagnosis for hallucination, safety, and TTS formatting.
    Manages the retry loop.
    """
    logger.info("---SAFETY CRITIC NODE---")

    # Increment Retry Count
    current_retries = state.get("retry_count", 0)
    new_retry_count = current_retries + 1
    logger.info(f"Critic Evaluation - Attempt {new_retry_count}/{MAX_RETRIES + 1}")

    # Check for Max Retries
    if current_retries >= MAX_RETRIES:
        logger.error("Max retries reached. Critic is rejecting the draft permanently.")
        return {
            "is_approved": False,
            "critic_feedback": "MAX_RETRIES_REACHED",
            "retry_count": new_retry_count
        }

    # Gather state variables
    draft = state.get("final_diagnosis", "")
    treatment_guide_doc = state.get("treatment_guide_doc", "")
    weather_constraints = state.get("weather_constraints", {})
    weather_context = state.get("weather_context", "")
    crop_age_days = state.get("crop_age_days", "Unknown")
    crop_stage = state.get("crop_stage", "Unknown")

    try:
        # Invoke Critic LLM
        evaluation = await safety_critic_chain.ainvoke({
            "treatment_guide_doc": treatment_guide_doc,
            "weather_constraints": weather_constraints,
            "weather_context": weather_context,
            "crop_age_days": crop_age_days,
            "crop_stage": crop_stage,
            "final_diagnosis": draft
        })
        
        is_approved = evaluation.is_approved
        critic_feedback = evaluation.critic_feedback
        
    except Exception:
        logger.exception("Critic LLM failed. Defaulting to rejection for safety.")
        is_approved = False
        critic_feedback = "Critic system encountered an error. Please rewrite safely."

    if is_approved:
        logger.info("Critic APPROVED the draft.")
    else:
        logger.warning(f"Critic REJECTED the draft. Reason: {critic_feedback}")

    # Return updates to state
    return {
        "is_approved": is_approved,
        "critic_feedback": critic_feedback,
        "retry_count": new_retry_count
    }    