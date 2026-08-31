"""ai_core/nodes/diagnosis_generator_node.py"""

import logging
from datetime import datetime, timezone
from typing import Any

from ai_core.chains.diagnosis_generator_chain import diagnosis_chain
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)


async def diagnosis_generator_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Synthesizes RAG truth data, weather, and farm history into a highly structured,
    farmer-friendly diagnosis and action plan. Handles critic retry loops.
    """
    logger.info("---DIAGNOSIS GENERATOR NODE---")

    #  Get exact current date for weather alignment
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # Extract context variables from state
    disease_name = state.get("disease_name", "Unknown Issue")
    treatment_guide_doc = state.get("treatment_guide_doc", "Consult a local expert.")
    weather_constraints = state.get("weather_constraints", {})

    # Extract live tools and timeline variables
    weather_context = state.get("weather_context", "Weather unavailable.")
    medical_timeline = state.get("medical_timeline", "No previous treatments.")
    crop_age_days = state.get("crop_age_days", "Unknown")
    crop_stage = state.get("crop_stage", "Unknown")

    # Extract Critic Feedback AND Previous Draft (if this is a retry loop)
    critic_feedback = state.get("critic_feedback", "")
    previous_draft = state.get("final_diagnosis", "")

    if critic_feedback:
        logger.warning("Generating Diagnosis (REVISION based on Critic Feedback).")
    else:
        logger.info(f"Generating Diagnosis (Initial Draft) for {disease_name}.")

    try:
        # Invoke the LLM
        final_diagnosis = await diagnosis_chain.ainvoke(
            {
                "current_date": current_date,
                "disease_name": disease_name,
                "treatment_guide_doc": treatment_guide_doc,
                "weather_constraints": weather_constraints,
                "weather_context": weather_context,
                "medical_timeline": medical_timeline,
                "crop_age_days": crop_age_days,
                "crop_stage": crop_stage,
                "previous_draft": previous_draft,
                "critic_feedback": critic_feedback,
            }
        )

    except Exception:
        logger.exception("Failed to generate diagnosis due to an LLM or network error.")
        final_diagnosis = None

    # Update the state
    return {"final_diagnosis": final_diagnosis}
