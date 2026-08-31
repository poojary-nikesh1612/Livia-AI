"""ai_core/nodes/vision_node.py"""

import logging
from typing import Any

from ai_core.chains.vision_chain import vision_chain
from ai_core.state import PaddyGraphState
from langchain_core.messages import HumanMessage
from schemas.ai_models import BatchVisionResult

logger = logging.getLogger(__name__)


# Provides image MIME type based on the leading base64 magic bytes.
def get_base64_mime_type(b64_string: str) -> str:
    """Inspects the leading base64 magic bytes to determine image MIME type."""
    if b64_string.startswith("/9j/"):
        return "image/jpeg"
    elif b64_string.startswith("iVBORw0KGgo"):
        return "image/png"
    elif b64_string.startswith("UklGR"):
        return "image/webp"
    elif b64_string.startswith("R0lGOD"):
        return "image/gif"
    return "image/jpeg"


def vision_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Evaluates a batch of images by invoking the vision LCEL chain.
    """
    logger.info("---VISION NODE---")

    base64_images = state.get("images", [])
    if not base64_images:
        logger.warning("Vision node called but no images found.")
        return {"is_image_rejected": True}

    # Human message content block with text and images
    content_blocks = [
        {
            "type": "text",
            "text": "Analyze these paddy plant images for visible disease symptoms, discoloration, and structural damage.",
        }
    ]

    for b64_img in base64_images:
        mime_type = get_base64_mime_type(b64_img)
        content_blocks.append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:{mime_type};base64,{b64_img}"},
            }
        )

    human_msg = HumanMessage(content=content_blocks)

    try:
        # Invoke the LCEL Chain passing the dynamic message block
        batch_result: BatchVisionResult = vision_chain.invoke(
            {"human_message_with_images": [human_msg]}
        )
    except Exception:
        logger.exception("Vision Chain failed.")
        return {"is_image_rejected": True}

    # Apply Filtering Logic
    valid_features = []
    for index, eval_obj in enumerate(batch_result.evaluations):
        if eval_obj.is_usable:
            valid_features.append(eval_obj.visual_features)
        else:
            logger.info(
                f"Image {index + 1} rejected. Reason: {eval_obj.visual_features}"
            )

    # 4. State Updates
    if not valid_features:
        logger.warning("All provided images were rejected by the Vision LLM.")
        return {"is_image_rejected": True}

    combined_visual_context = "\n".join(f"- {feature}" for feature in valid_features)
    logger.info(f"Extracted features:\n{combined_visual_context}")

    return {
        "is_image_rejected": False,
        "retry_count": 0,
        "visual_text": combined_visual_context,
    }
