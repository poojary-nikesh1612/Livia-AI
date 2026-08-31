"""ai_core/nodes/follow_up_generation_node.py"""

import logging
from datetime import datetime, timezone
from typing import Any

from ai_core.chains.follow_up_generator_chain import follow_up_chain
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)


async def follow_up_generation_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Answers farmer follow-up questions using recent chat history, live weather,
    and farm timelines. Formatted for voice delivery and routed to safety critic.
    """
    logger.info("---FOLLOW-UP GENERATION NODE---")

    #  Get exact current date for weather alignment
    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")

    # User Inputs & History
    user_text = state.get("user_text", "")
    chat_history = state.get("recent_chat_history", "No previous chat history.")

    # Live Context Variables
    weather_context = state.get("weather_context", "Weather unavailable.")
    medical_timeline = state.get("medical_timeline", "No previous treatments.")
    crop_age_days = state.get("crop_age_days", "Unknown")
    crop_stage = state.get("crop_stage", "Unknown")

    # Extract Critic Feedback AND Previous Draft (if this is a retry loop)
    critic_feedback = state.get("critic_feedback", "")
    previous_draft = state.get("final_diagnosis", "")

    if critic_feedback:
        logger.warning("Generating Follow-up (REVISION based on Critic Feedback).")
    else:
        logger.info("Generating Follow-up (Initial Draft).")

    try:
        # Invoke the LLM
        follow_up_answer = await follow_up_chain.ainvoke(
            {
                "current_date": current_date,
                "weather_context": weather_context,
                "crop_age_days": crop_age_days,
                "crop_stage": crop_stage,
                "medical_timeline": medical_timeline,
                "critic_feedback": critic_feedback,
                "previous_draft": previous_draft,
                "chat_history": chat_history,
                "user_text": user_text,
            }
        )

    except Exception:
        logger.exception(
            "Failed to generate follow-up answer due to LLM or network error."
        )
        follow_up_answer = None

    # Update the state
        return {"final_diagnosis": follow_up_answer}
