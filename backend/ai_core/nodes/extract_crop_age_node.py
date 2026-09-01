"""ai_core/nodes/extract_crop_age_node.py"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any
import uuid
from database.postgres_ai import create_crop_cycle
from ai_core.constants import CONTEXT_LOADER_NODE
from ai_core.llm_config import lightweight_llm
from ai_core.state import PaddyGraphState
from ai_core.utils.agronomy import calculate_paddy_stage
from schemas.ai_models import CropAgeExtraction

logger = logging.getLogger(__name__)

# Prevent infinite loops
MAX_RETRIES = 2

async def extract_crop_age_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Uses the lightweight Gemma model to parse fuzzy text into exact days.
    """
    farmer_answer = state.get("clarification_answer", "")
    retry_count = state.get("retry_count", 0)
    user_id = state.get("user_id")

    logger.info(f"Extracting crop age from text: '{farmer_answer}'")

    # Call the lightweight LLM with structured output
    structured_llm = lightweight_llm.with_structured_output(CropAgeExtraction)

    prompt = (
        f"Extract the crop age from the following user input: '{farmer_answer}'. "
        "Calculate the approximate age in days."
    )

    try:
        result: CropAgeExtraction = structured_llm.ainvoke(prompt)
    except Exception:
        logger.exception(f"LLM parsing failed for input: '{farmer_answer}'")
        result = CropAgeExtraction(is_understood=False, age_in_days=None)

    # Handle Failure to extract age (either not understood or no days found)
    if not result.is_understood or result.age_in_days is None:
        new_retry = retry_count + 1

        # Check for Max Retries
        if new_retry >= MAX_RETRIES:
            return {
                "final_diagnosis": "I couldn't determine the crop age, so I had to stop. Please start again and tell me the crop age.",
                "paused_by": "fatal_error",
                "have_question": False,
            }

        # First failure -> Ask again
        return {
            "have_question": True,
            "clarifying_question": "I couldn't understand the crop age. Please tell me how old the crop is, for example, 45 days or 3 weeks.",
            "retry_count": new_retry,
            "paused_by": CONTEXT_LOADER_NODE,
            "clarification_answer": None,
        }

    age_days = result.age_in_days
    planting_date_obj = datetime.now(timezone.utc) - timedelta(days=age_days)
    planting_date_iso = planting_date_obj.strftime("%Y-%m-%d")
    crop_stage = calculate_paddy_stage(age_days)

    new_cycle_id = None
    if user_id:
        try:
            new_cycle_id = await create_crop_cycle(
                user_id=uuid.UUID(str(user_id)), 
                planting_date=planting_date_obj.date()
            )
        except Exception :
            logger.exception("Failed to create crop cycle DB record")

    return {
        "cycle_id": str(new_cycle_id) if new_cycle_id else None,
        "crop_age_days": age_days,
        "planting_date": planting_date_iso,
        "crop_stage": crop_stage,
        "retry_count": 0,
        "paused_by": None,
        "clarifying_question": None,
        "clarification_answer": None,
        "have_question": False,
    }
