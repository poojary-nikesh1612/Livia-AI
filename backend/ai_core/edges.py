"""ai_core/edges.py"""

import logging

from ai_core import constants as consts
from ai_core.state import PaddyGraphState
from langgraph.graph import END

logger = logging.getLogger(__name__)


# Routing function after context is loaded
def route_after_context_loader(state: PaddyGraphState) -> str:
    """
    Traffic cop after context is loaded.
    If we don't know the crop cycle (cycle_id is None), route to onboarding.
    If we do, proceed directly to the main AI router.
    """
    if not state.get("cycle_id"):
        return consts.ONBOARDING_NODE

    return consts.ROUTER_NODE


# Routing function after human input
def route_after_human_input(state: PaddyGraphState) -> str:
    """
    Determines where the graph should go after the human-in-the-loop resumes.
    It reads the 'paused_by' attribute to return to the exact phase that asked for help.
    """
    paused_by = state.get("paused_by")

    logger.info(f"Routing after human input. Paused originally by: {paused_by}")

    # Fatal Error (Max retries reached)
    if paused_by == "fatal_error":
        logger.info("User failed to provide requested information. Routing to END.")
        return END

    # Onboarding Phase
    if paused_by == consts.ONBOARDING_NODE:
        return consts.EXTRACT_CROP_AGE_NODE

    # Vision Phase
    elif paused_by == consts.REQUEST_IMAGE_NODE:
        return consts.VISION_NODE

    # Symptom Alignment Phase
    elif paused_by == consts.SYMPTOM_ALIGNMENT_NODE:
        return consts.SYMPTOM_ALIGNMENT_NODE

    # Investigative question Phase
    elif paused_by == consts.INVESTIGATIVE_QUESTION_NODE:
        return consts.SYMPTOM_REFINEMENT_NODE

    # Fallback failsafe
    logger.warning(
        f"Unknown pause origin: {paused_by}. Defaulting to Universal Fallback."
    )
    return consts.UNIVERSAL_FALLBACK_NODE


# Routing function after crop age extraction
def route_after_extract_crop_age(state: PaddyGraphState) -> str:
    """
    Traffic cop after we attempt to extract the crop age from the user's text.
    handles success, retry loops, and graceful failures.
    """
    paused_by = state.get("paused_by")
    have_question = state.get("have_question")

    # CASE 1: Fatal Error (Max retries reached)
    if paused_by == "fatal_error":
        logger.info("Crop age extraction failed max retries. Routing to END.")
        return END

    # CASE 2: Retry Loop
    if have_question:
        logger.info(
            "Crop age extraction failed once. Routing to the human input node for retry."
        )
        return consts.HUMAN_INPUT_NODE

    # CASE 3: Success
    logger.info("Crop age extraction successful. Proceeding to the router node.")
    return consts.ROUTER_NODE


# Routing function after router node
def route_after_router(state: PaddyGraphState) -> str:
    """
    Conditional edge that reads the exact destination decided by
    the Router Node and directs traffic to that specific node.
    """
    destination = state.get("router_destination")

    # If the state is somehow missing the key, default to the general chat node
    if not destination:
        logger.warning(
            "Router destination missing in state. Defaulting to general chat."
        )
        return consts.GENERAL_CHAT_NODE

    # If it's follow up, intercept and send to Context Enrichment
    if destination == consts.FOLLOW_UP_GENERATION_NODE:
        logger.info(
            f"Traffic Control: Intercepting Follow-up. Routing to {consts.CONTEXT_ENRICHMENT_NODE}"
        )
        return consts.CONTEXT_ENRICHMENT_NODE
    logger.info(f"Traffic Control: Routing to {destination}")

    return destination


# Routing function after request image node
def route_after_request_image(state: PaddyGraphState) -> str:
    """
    Determines where to go after request image node.
    Routes to END on a fatal error, or to the human input node to pause for upload.
    """
    paused_by = state.get("paused_by")

    # 1. Fatal Error (Max retries hit) -> Exit Graph entirely
    if paused_by == "fatal_error":
        logger.info("Traffic Control: Fatal error detected. Routing to END.")
        return END

    # 2. Normal Request -> Route to Human Input
    logger.info("Traffic Control: Image requested. Routing to human input node.")
    return consts.HUMAN_INPUT_NODE


# Routing function after vision node
def route_after_vision(state: PaddyGraphState) -> str:
    """
    Traffic controller after the Vision LLM evaluates the batch of images.
    Routes to request a new image if they were bad, or to the alignment/reasoning
    node if they successfully yielded visual features.
    """
    is_rejected = state.get("is_image_rejected", False)

    if is_rejected:
        logger.info(
            "Traffic Control: Images were rejected by Vision. Routing to the request image node."
        )
        return consts.REQUEST_IMAGE_NODE

    logger.info(
        "Traffic Control: Visual features extracted successfully. Routing to the symptom alignment node."
    )
    return consts.SYMPTOM_ALIGNMENT_NODE


# Routing function after symptom alignment node
def route_after_alignment(state: PaddyGraphState) -> str:
    """
    Traffic controller after the Symptom Alignment Node.
    Routes to the human to answer the clarifying question, or
    progresses to the RAG database search if the context is clear.
    """
    have_question = state.get("have_question", False)

    if have_question:
        logger.info(
            "Traffic Control: Mismatch found. Routing to the human input node for clarification."
        )
        return consts.HUMAN_INPUT_NODE

    logger.info("Traffic Control: Symptoms aligned. Routing to the RAG search node.")
    return consts.RAG_SEARCH_NODE


# Routing function after RAG search node
def route_after_rag_search(state: PaddyGraphState) -> str:
    """
    Checks if RAG found any candidate diseases.
    If empty, route to the universal fallback node. If not, route to the Reranker
    """
    chunks = state.get("retrieved_candidate_chunks", [])

    if not chunks:
        logger.warning(
            "RAG search returned 0 results. Route to the universal fallback node."
        )
        return consts.UNIVERSAL_FALLBACK_NODE

    logger.info(f"RAG found {len(chunks)} chunks. Routing to Reranker.")
    return consts.RERANKER_NODE


# Routing function after Reranker node
def route_after_reranking(state: PaddyGraphState) -> str:
    score = state.get("top_candidate_score", 0.0)

    if score >= 0.85:
        return consts.FETCH_TREATMENT_NODE
    else:
        # If failed to get a confident match, we go to ask a targeted question
        return consts.INVESTIGATIVE_QUESTION_NODE


# Routing function after Investigative Question node
def route_after_investigation(state: PaddyGraphState) -> str:
    """
    Traffic controller after the Investigative Question Node.
    Routes to the human to answer the new question, or to the
    Universal Fallback Node if the max retry limit was reached.
    """
    have_question = state.get("have_question", False)

    if have_question:
        logger.info(
            "Traffic Control: Investigative question generated. Routing to the human input node."
        )
        return consts.HUMAN_INPUT_NODE

    logger.warning(
        "Traffic Control: No question generated (likely max retries). Routing to the universal fallback node."
    )
    return consts.UNIVERSAL_FALLBACK_NODE


# Routing function after Fetch Treatment node
def route_after_fetch_treatment(state: PaddyGraphState) -> str:
    """
    Traffic controller after fetching the treatment guide from the database.
    If the fetch failed (doc is None), we route to the Universal Fallback.
    Otherwise, we proceed to generate the final response.
    """
    treatment_doc = state.get("treatment_guide_doc")

    if not treatment_doc:
        logger.error(
            "Traffic Control: Treatment document is None. Routing to the universal fallback node."
        )
        return consts.UNIVERSAL_FALLBACK_NODE

    logger.info(
        "Traffic Control: Treatment document found. Proceeding to the next step."
    )
    return consts.CONTEXT_ENRICHMENT_NODE


# Routing function after Context Enrichment Node
def route_after_context_enrichment(state: PaddyGraphState) -> str:
    """
    Routes from Context Enrichment to the correct generator based on the initial intent.
    """
    router_dest = state.get("router_destination")

    if not router_dest:
        logger.warning(
            "Traffic Control: router_destination missing. Routing to Fallback."
        )
        return consts.UNIVERSAL_FALLBACK_NODE

    # Check if the initial intent was follow-up
    if router_dest == consts.FOLLOW_UP_GENERATION_NODE:
        logger.info(f"Traffic Control: Routing to {consts.FOLLOW_UP_GENERATION_NODE}.")
        return consts.FOLLOW_UP_GENERATION_NODE

    # Otherwise, it must have come from the Diagnosis RAG flow
    logger.info(f"Traffic Control: Routing to {consts.DIAGNOSIS_GENERATOR_NODE}.")
    return consts.DIAGNOSIS_GENERATOR_NODE


# Routing function after generation node
def route_after_generation(state: PaddyGraphState) -> str:
    """
    If generation failed (None), go to fallback.
    Otherwise, send the draft to the Critic for safety review.
    """
    if not state.get("final_diagnosis"):
        logger.error("Traffic Control: No diagnosis generated. Routing to Fallback.")
        return consts.UNIVERSAL_FALLBACK_NODE

    logger.info("Traffic Control: Diagnosis generated. Routing to Safety Critic.")
    return consts.SAFETY_CRITIC_NODE


# Routing function after Safety Critic Node
def route_after_critic(state: PaddyGraphState) -> str:
    """
    Routes traffic based on the Critic's approval and the retry limits.
    """
    is_approved = state.get("is_approved")
    feedback = state.get("critic_feedback")

    if is_approved:
        logger.info("Traffic Control: Draft approved! Ending workflow successfully.")
        return END 
    if feedback == "MAX_RETRIES_REACHED":
        logger.error("Traffic Control: Max retries hit. Routing to Fallback.")
        return consts.UNIVERSAL_FALLBACK_NODE
        
    logger.info("Traffic Control: Draft rejected. Routing back to Generator for rewrite.")
    
   # Send it back to the node that routed to the safety critic (diagnosis or follow-up generator).
    router_dest = state.get("router_destination")
    if router_dest == consts.FOLLOW_UP_GENERATION_NODE:
        return consts.FOLLOW_UP_GENERATION_NODE
        
    return consts.DIAGNOSIS_GENERATOR_NODE