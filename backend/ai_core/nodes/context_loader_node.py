"""ai_core/nodes/context_loader_node.py: Initial state hydration node."""

import logging
from datetime import datetime, timezone
from typing import Any

from database.postgres_ai import get_active_crop_context, get_recent_chat_history
from ai_core.constants import CONTEXT_LOADER_NODE
from ai_core.state import PaddyGraphState
from ai_core.utils.agronomy import calculate_paddy_stage

logger = logging.getLogger(__name__)


async def context_loader_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Fetches the active crop cycle, GPS coordinates, computes crop age in days,
    and pulls the last 6 chat messages for short-term pronoun resolution.
    """
    user_id = state.get("user_id")
    if not user_id:
        logger.error("load_context_node invoked without user_id in state.")
        return {"cycle_id": None}

    crop_ctx = await get_active_crop_context(user_id)

    # If no active cycle exists, leave cycle_id as None
    if not crop_ctx:
        logger.info(f"No active crop cycle found for user {user_id}")
        return {
            "cycle_id": None,
            "crop_age_days": None,
            "planting_date": None,
            "recent_chat_history": [],
            "have_question": True,
            "clarifying_question":"How many days old is your paddy crop?",
            "paused_by": CONTEXT_LOADER_NODE,
        }

    cycle_id = crop_ctx["cycle_id"]
    planting_date_str = crop_ctx["planting_date"]
    lat = crop_ctx["farm_latitude"]
    lon = crop_ctx["farm_longitude"]

    # 2. Compute exact crop age
    crop_age_days = None
    if planting_date_str:
        try:
            planting_date = datetime.fromisoformat(planting_date_str).date()
            today = datetime.now(timezone.utc)
            crop_age_days = max(0, (today.date() - planting_date).days)
        except ValueError:
            logger.warning(
                f"Invalid planting_date format encountered: {planting_date_str}"
            )

    # 3. Derive crop stage from age
    crop_stage = None
    crop_stage = calculate_paddy_stage(crop_age_days)

    # 4. Fetch the last 6 messages
    recent_history = await get_recent_chat_history(cycle_id=cycle_id)

    # 5. Return state updates
    return {
        "cycle_id": cycle_id,
        "planting_date": planting_date_str,
        "crop_age_days": crop_age_days,
        "crop_stage": crop_stage,
        "location": (
            {"lat": lat, "lon": lon} if (lat is not None and lon is not None) else None
        ),
        "recent_chat_history": recent_history,
    }
