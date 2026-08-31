"""ai_core/nodes/rag_search_node.py"""

import logging
from typing import Any

from ai_core.state import PaddyGraphState
from database.vector_db import search_disease_by_symptoms

logger = logging.getLogger(__name__)


async def rag_search_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Executes a semantic vector search using the highly descriptive
    aligned_symptom_profile to fetch candidate diseases.
    """
    logger.info("---RAG SEARCH NODE---")

    symptoms_query = state.get("aligned_symptom_profile", "")
    crop_stage = state.get("crop_stage")

    # Empty Query
    if not symptoms_query:
        logger.warning("No aligned_symptom_profile found in state. Skipping search.")
        return {"retrieved_candidate_chunks": []}

    # Extract and format the crop stage
    valid_stage =""
    if crop_stage:
        valid_stage = crop_stage.value
    else:
        logger.warning("No crop_stage found in state. Vector search may return empty.")

    logger.info(
        f"Executing RAG Search. Stage: {valid_stage} | Query: '{symptoms_query[:75]}...'"
    )

    # The semantic search
    try:
        retrieved_chunks = await search_disease_by_symptoms(
            symptoms_query=symptoms_query, valid_stage=valid_stage
        )
    except Exception:
        logger.exception("RAG search failed")
        return {"retrieved_candidate_chunks": []}

    logger.info(
        f"Successfully retrieved {len(retrieved_chunks)} candidate chunks from PGVector."
    )

    # State Update
    return {"retrieved_candidate_chunks": retrieved_chunks}
