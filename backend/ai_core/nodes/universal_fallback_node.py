"""ai_core/nodes/universal_fallback_node.py"""

import logging
from typing import Any

from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)


def universal_fallback_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    A universal safety node triggered when the graph cannot proceed.
    Handles empty RAG results, API failures, or missing critical data.
    """
    logger.warning("---UNIVERSAL FALLBACK NODE TRIGGERED---")

    # Generalized response for failure.
    fallback_message = (
        "I apologize, but I could not find a confident match or encountered an issue processing the data "
        "for these specific symptoms. To ensure your crop gets the right care, please consult a local "
        "agricultural expert or try again with clearer photos and descriptions."
    )

    return {
        "final_diagnosis": fallback_message,
    }
