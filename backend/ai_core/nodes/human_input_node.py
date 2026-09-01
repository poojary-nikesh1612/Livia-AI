"""ai_core/nodes/human_input_node.py"""

import logging
from typing import Any

from ai_core.constants import (
    INVESTIGATIVE_QUESTION_NODE,
    CONTEXT_LOADER_NODE,
    REQUEST_IMAGE_NODE,
)
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)

SYSTEM_PAUSE_NODES = {CONTEXT_LOADER_NODE, REQUEST_IMAGE_NODE,INVESTIGATIVE_QUESTION_NODE}


async def human_input_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Executes immediately after the graph resumes from a human-in-the-loop pause.
    Safely bridges user input (text or images) into the state.
    """
    farmer_answer = state.get("clarification_answer")
    question_asked = state.get("clarifying_question")
    paused_by = state.get("paused_by")
    existing_histories = state.get("clarification_history", {})
    new_images = state.get("new_uploaded_images", [])

    updates: dict[str, Any] = {
        "have_question": False,
        "new_uploaded_images": [],
    }

    if paused_by == REQUEST_IMAGE_NODE:
        if not new_images:
            # The user ignored our request for an image!
            logger.warning("User failed to provide requested image. Aborting.")
            updates["paused_by"] = ("fatal_error")
            updates["final_diagnosis"] = (
                "I need a photo to continue. Please start again with a clear photo."
            )
            return updates
        else:
            # Success! Overwrite the old images with the new ones.
            updates["images"] = new_images

    # Only save if it's an AI node (not system nodes)
    if paused_by and paused_by not in SYSTEM_PAUSE_NODES:
        new_entries = []
        if question_asked:
            new_entries.append({"role": "assistant", "content": question_asked})
        if farmer_answer:
            new_entries.append({"role": "user", "content": farmer_answer})

        if new_entries:
            # 1. Get the specific history for THIS node (or start fresh if it's new)
            current_node_history = existing_histories.get(paused_by, [])

            # 2. Make a copy of the whole dictionary
            new_histories = dict(existing_histories)

            # 3. Update ONLY this node's history
            new_histories[paused_by] = current_node_history + new_entries

            # 4. Save it back to state
            updates["clarification_history"] = new_histories

    return updates
