"""ai_core/nodes/fetch_treatment_node.py"""

import logging
from typing import Any

from ai_core.state import PaddyGraphState
from database.postgres_ai import get_treatment_by_disease_id

logger = logging.getLogger(__name__)


async def fetch_treatment_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Fetches the definitive treatment guide, standardized name, and weather constraints
    from the PostgreSQL relational database using the top candidate disease ID.
    """
    logger.info("---FETCH TREATMENT NODE---")

    disease_id = state.get("top_candidate_disease_id")

    # Safety check
    if not disease_id:
        logger.error("No disease_id found in state. Cannot fetch treatment.")
        return {
            "disease_name": None,
            "treatment_guide_doc": None,
            "weather_constraints": None,
        }

    logger.info(f"Fetching relational truth data for disease_id: {disease_id}")

    try:
        # Execute the direct DB lookup
        record = await get_treatment_by_disease_id(disease_id)

        # Map the dictionary from the DB to state
        return {
            "disease_name": record.get("disease_name"),
            "treatment_guide_doc": record.get("treatment_guide"),
            "weather_constraints": record.get("weather_constraints"),
        }

    except Exception:
        logger.exception(f"Database lookup failed for disease_id {disease_id}")
        return {
            "disease_name": None,
            "treatment_guide_doc":None,
            "weather_constraints": None,
        }
