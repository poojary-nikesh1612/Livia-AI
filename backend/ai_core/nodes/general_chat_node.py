"""ai_core/nodes/general_chat_node.py"""

import logging
from typing import Any

from ai_core.chains.general_chat_chain import general_chat_chain
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)


def general_chat_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Handles out-of-bounds questions, greetings, and identity checks.
    Acts as a conversational guardrail for the system.
    """
    user_text = state.get("user_text", "")

    logger.info(f"General Chat Node activated for input: '{user_text}'")

    try:
        # 2. Call the LLM
        final_answer = general_chat_chain.invoke({"user_text": user_text})

    except Exception:
        logger.exception("General Chat LLM failed")
        final_answer = "I apologize, but I am having trouble connecting right now. I am Livia, your paddy assistant—please try asking your question again in a moment."

    logger.info("General Chat Node completed successfully.")

    # 3. Update the state with the final text
    return {"final_diagnosis": final_answer}
