"""ai_core/nodes/reranker_node.py"""

import logging
from typing import Any

from ai_core.chains.reranker_chain import cloudflare_reranker_chain
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)


async def reranker_node(state: PaddyGraphState) -> dict[str, Any]:
    """
    Takes retrieved candidate chunks and passes them through the Cloudflare Reranker chain.
    Updates the state with the reordered chunks, top candidate ID, and top score.
    """
    logger.info("---RERANKER NODE---")

    chunks = state.get("retrieved_candidate_chunks", [])
    query = state.get("aligned_symptom_profile", "")

    if not chunks:
        logger.warning("No candidate chunks available to rerank.")
        return {
            "retrieved_candidate_chunks": [],
            "top_candidate_disease_id": None,
            "top_candidate_score": None,
        }

    logger.info(f"Invoking Reranker Chain for {len(chunks)} chunks.")

    # Invoke the LCEL chain 
    try:
        reranked_chunks = await cloudflare_reranker_chain.ainvoke(
            {"query": query, "chunks": chunks}
        )
    except Exception:
        logger.exception(
            "Reranker chain execution failed. Falling back to default order."
        )

        # Graceful fallback: preserve original chunks and assign synthetic scores
        reranked_chunks = chunks
        for idx, chunk in enumerate(reranked_chunks):
            chunk["metadata"]["relevance_score"] = 1.0 / (idx + 1)

    # Extract the top candidate details from the newly sorted list
    top_candidate = reranked_chunks[0]
    top_metadata = top_candidate.get("metadata", {})

    top_disease_id = top_metadata.get("disease_id")
    top_score = top_metadata.get("relevance_score")
    second_score = (
        reranked_chunks[1].get("metadata", {}).get("relevance_score")
        if len(reranked_chunks) >= 2
        else None
    )

    top_score_str = f"{top_score:.4f}" if top_score is not None else "N/A"
    second_score_str = f"{second_score:.4f}" if second_score is not None else "N/A"
    margin_str = (
        f"{(float(top_score) - float(second_score)):.4f}"
        if (top_score is not None and second_score is not None)
        else "N/A"
    )

    logger.info(
        f"Reranking complete. Top Match Disease ID: {top_disease_id} "
        f"(Top-1 Score: {top_score_str}, Top-2 Score: {second_score_str}, Margin: {margin_str})"
    )

    # Return updated fields to the graph state
    return {
        "retrieved_candidate_chunks": reranked_chunks,
        "top_candidate_disease_id": top_disease_id,
        "top_candidate_score": top_score,
    }
