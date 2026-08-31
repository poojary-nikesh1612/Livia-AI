"""ai_core/nodes/onboarding_node.py"""

import random
from typing import Any

from ai_core.constants import ONBOARDING_NODE
from ai_core.state import PaddyGraphState

CROP_AGE_QUESTIONS = [
    "How old is your paddy crop?",
    "Can you tell me the age of your crop?",
    "How many days ago did you plant your paddy?",
    "When did you plant your crop?",
    "How much time has passed since planting?",
]


def onboarding_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Randomly selects a simple onboarding question to ask the farmer.
    After this node executes, the graph will attempt to move to the
    human_input_node and be paused by the checkpointer.
    """
    question = random.choice(CROP_AGE_QUESTIONS)

    return {
        "have_question": True,
        "clarifying_question": question,
        "paused_by": ONBOARDING_NODE,
    }
