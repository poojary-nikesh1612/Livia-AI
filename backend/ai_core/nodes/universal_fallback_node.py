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
        "I couldn't understand the problem with your crop. Please try again with a clear photo and some details about the problem. You can also contact a local agricultural expert for help."
    )

    return {
        "final_diagnosis": fallback_message,
    }
