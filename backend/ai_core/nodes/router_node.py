"""ai_core/nodes/router_node.py"""

import logging
from typing import Any

from ai_core.chains.router_chain import router_chain
from ai_core.constants import (
    FOLLOW_UP_GENERATION_NODE,
    GENERAL_CHAT_NODE,
    REQUEST_IMAGE_NODE,
    VISION_NODE,
)
from ai_core.state import PaddyGraphState
from schemas.ai_models import RouteDecision

logger = logging.getLogger(__name__)

# Dictionary to map Pydantic literals to your official constants
ROUTER_MAPPING = {
    "general_chat_node": GENERAL_CHAT_NODE,
    "follow_up_generation_node": FOLLOW_UP_GENERATION_NODE,
    "request_image_node": REQUEST_IMAGE_NODE,
    "vision_node": VISION_NODE,
}


def router_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Evaluates main user input with full conversational context and routes to 1 of 4 specialized paths.
    """
    # Gather main state variables
    user_text = state.get("user_text", "")
    has_images = len(state.get("images", [])) > 0
    recent_history_str = state.get("recent_chat_history", "No previous history.")

    logger.info(f"Router analyzing input: '{user_text}'. Images present: {has_images}")

    try:
        decision: RouteDecision = router_chain.invoke(
            {
                "has_images": has_images,
                "chat_history": recent_history_str,
                "user_text": user_text,
            }
        )

        logger.info(
            f"Router decided: {decision.destination}. Reason: {decision.reasoning}"
        )

        next_node = ROUTER_MAPPING.get(decision.destination, GENERAL_CHAT_NODE)

    except Exception:
        logger.exception("Router LLM failed. Defaulting to general chat.")
        next_node = GENERAL_CHAT_NODE

    # Update the state
    return {"router_destination": next_node}
