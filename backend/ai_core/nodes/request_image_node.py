"""ai_core/nodes/request_image_node.py"""

import logging
from typing import Any

from ai_core.constants import REQUEST_IMAGE_NODE
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)

# Prevent infinite loops
MAX_RETRIES = 2

def request_image_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Handles requesting an image from the user.
    Uses the global `retry_count` to enforce a 1-retry limit.
    """
    logger.info("---REQUEST IMAGE NODE---")

    is_rejected = state.get("is_image_rejected", False)
    retry_count = state.get("retry_count", 0)

    # Vision node rejected the image
    if is_rejected:
        new_retry = retry_count + 1

        # Max retries reached -> Graceful Exit
        if new_retry >= MAX_RETRIES:
            logger.warning("Image retry limit exceeded. Aborting.")
            return {
                "final_diagnosis": "I cannot analyze these images. They are not clear. Please start again later and upload a clear photo of the plant.",
                "paused_by": "fatal_error",
                "have_question": False,
                "is_image_rejected": False,
                "retry_count": 0,
            }

        # First rejection -> Ask again
        question = "I cannot see the paddy plant clearly in this image. Please upload a new, clear photos."

    # Router requested image
    else:
        new_retry = 0
        question = "I need to see the plant to answer this. Please upload a clear photo of your paddy crop."

    return {
        "clarifying_question": question,
        "have_question": True,
        "paused_by": REQUEST_IMAGE_NODE,
        "retry_count": new_retry,
        "is_image_rejected": False,
        "clarification_answer": None,
    }
