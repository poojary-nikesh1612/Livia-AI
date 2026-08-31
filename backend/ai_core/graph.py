"""ai_core/graph.py"""

import logging

from langgraph.graph import END, StateGraph

from ai_core import constants as consts
from ai_core import edges
from ai_core.nodes import (
    context_enrichment_node,
    context_loader_node,
    diagnosis_generator_node,
    extract_crop_age_node,
    fetch_treatment_node,
    follow_up_generation_node,
    general_chat_node,
    human_input_node,
    investigative_question_node,
    onboarding_node,
    rag_search_node,
    request_image_node,
    reranker_node,
    router_node,
    safety_critic_node,
    symptom_alignment_node,
    symptom_refinement_node,
    universal_fallback_node,
    vision_node,
)
from ai_core.state import PaddyGraphState

logger = logging.getLogger(__name__)


def build_uncompiled_graph() -> StateGraph:
    """
    Builds the uncompiled StateGraph workflow 
    """
    logger.info("Building uncompiled PaddyGraph workflow...")
    workflow = StateGraph(PaddyGraphState)

    workflow.add_node(consts.CONTEXT_LOADER_NODE, context_loader_node.context_loader_node)
    workflow.add_node(consts.ONBOARDING_NODE, onboarding_node.onboarding_node)
    workflow.add_node(consts.HUMAN_INPUT_NODE, human_input_node.human_input_node)
    workflow.add_node(consts.ROUTER_NODE, router_node.router_node)
    workflow.add_node(consts.VISION_NODE, vision_node.vision_node)
    workflow.add_node(
        consts.EXTRACT_CROP_AGE_NODE, extract_crop_age_node.extract_crop_age_node
    )
    workflow.add_node(
        consts.FOLLOW_UP_GENERATION_NODE,
        follow_up_generation_node.follow_up_generation_node,
    )
    workflow.add_node(consts.REQUEST_IMAGE_NODE, request_image_node.request_image_node)
    workflow.add_node(consts.GENERAL_CHAT_NODE, general_chat_node.general_chat_node)
    workflow.add_node(
        consts.SYMPTOM_ALIGNMENT_NODE, symptom_alignment_node.symptom_alignment_node
    )
    workflow.add_node(consts.RAG_SEARCH_NODE, rag_search_node.rag_search_node)
    workflow.add_node(
        consts.UNIVERSAL_FALLBACK_NODE, universal_fallback_node.universal_fallback_node
    )
    workflow.add_node(consts.RERANKER_NODE, reranker_node.reranker_node)
    workflow.add_node(
        consts.FETCH_TREATMENT_NODE, fetch_treatment_node.fetch_treatment_node
    )
    workflow.add_node(
        consts.INVESTIGATIVE_QUESTION_NODE,
        investigative_question_node.investigative_question_node,
    )
    workflow.add_node(
        consts.SYMPTOM_REFINEMENT_NODE, symptom_refinement_node.symptom_refinement_node
    )
    workflow.add_node(
        consts.CONTEXT_ENRICHMENT_NODE, context_enrichment_node.context_enrichment_node
    )
    workflow.add_node(
        consts.DIAGNOSIS_GENERATOR_NODE,
        diagnosis_generator_node.diagnosis_generator_node,
    )
    workflow.add_node(consts.SAFETY_CRITIC_NODE, safety_critic_node.safety_critic_node)

    workflow.set_entry_point(consts.CONTEXT_LOADER_NODE)

    workflow.add_conditional_edges(
        consts.CONTEXT_LOADER_NODE,
        edges.route_after_context_loader,
        {
            consts.ONBOARDING_NODE: consts.ONBOARDING_NODE,
            consts.ROUTER_NODE: consts.ROUTER_NODE,
        },
    )

    workflow.add_edge(consts.ONBOARDING_NODE, consts.HUMAN_INPUT_NODE)

    workflow.add_conditional_edges(
        consts.HUMAN_INPUT_NODE,
        edges.route_after_human_input,
        {
            END: END,
            consts.EXTRACT_CROP_AGE_NODE: consts.EXTRACT_CROP_AGE_NODE,
            consts.VISION_NODE: consts.VISION_NODE,
            consts.SYMPTOM_ALIGNMENT_NODE: consts.SYMPTOM_ALIGNMENT_NODE,
            consts.SYMPTOM_REFINEMENT_NODE: consts.SYMPTOM_REFINEMENT_NODE,
            consts.UNIVERSAL_FALLBACK_NODE: consts.UNIVERSAL_FALLBACK_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.EXTRACT_CROP_AGE_NODE,
        edges.route_after_extract_crop_age,
        {
            END: END,
            consts.HUMAN_INPUT_NODE: consts.HUMAN_INPUT_NODE,
            consts.ROUTER_NODE: consts.ROUTER_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.ROUTER_NODE,
        edges.route_after_router,
        {
            consts.GENERAL_CHAT_NODE: consts.GENERAL_CHAT_NODE,
            consts.REQUEST_IMAGE_NODE: consts.REQUEST_IMAGE_NODE,
            consts.VISION_NODE: consts.VISION_NODE,
            consts.CONTEXT_ENRICHMENT_NODE: consts.CONTEXT_ENRICHMENT_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.REQUEST_IMAGE_NODE,
        edges.route_after_request_image,
        {
            END: END,
            consts.HUMAN_INPUT_NODE: consts.HUMAN_INPUT_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.VISION_NODE,
        edges.route_after_vision,
        {
            consts.REQUEST_IMAGE_NODE: consts.REQUEST_IMAGE_NODE,
            consts.SYMPTOM_ALIGNMENT_NODE: consts.SYMPTOM_ALIGNMENT_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.SYMPTOM_ALIGNMENT_NODE,
        edges.route_after_alignment,
        {
            consts.HUMAN_INPUT_NODE: consts.HUMAN_INPUT_NODE,
            consts.RAG_SEARCH_NODE: consts.RAG_SEARCH_NODE,
        },
    )


    workflow.add_conditional_edges(
        consts.RAG_SEARCH_NODE,
        edges.route_after_rag_search,
        {
            consts.UNIVERSAL_FALLBACK_NODE: consts.UNIVERSAL_FALLBACK_NODE,
            consts.RERANKER_NODE: consts.RERANKER_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.RERANKER_NODE,
        edges.route_after_reranking,
        {
            consts.FETCH_TREATMENT_NODE: consts.FETCH_TREATMENT_NODE,
            consts.INVESTIGATIVE_QUESTION_NODE: consts.INVESTIGATIVE_QUESTION_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.INVESTIGATIVE_QUESTION_NODE,
        edges.route_after_investigation,
        {
            consts.HUMAN_INPUT_NODE: consts.HUMAN_INPUT_NODE,
            consts.UNIVERSAL_FALLBACK_NODE: consts.UNIVERSAL_FALLBACK_NODE,
        },
    )

    workflow.add_edge(consts.SYMPTOM_REFINEMENT_NODE, consts.RAG_SEARCH_NODE)

    workflow.add_conditional_edges(
        consts.FETCH_TREATMENT_NODE,
        edges.route_after_fetch_treatment,
        {
            consts.UNIVERSAL_FALLBACK_NODE: consts.UNIVERSAL_FALLBACK_NODE,
            consts.CONTEXT_ENRICHMENT_NODE: consts.CONTEXT_ENRICHMENT_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.CONTEXT_ENRICHMENT_NODE,
        edges.route_after_context_enrichment,
        {
            consts.UNIVERSAL_FALLBACK_NODE: consts.UNIVERSAL_FALLBACK_NODE,
            consts.FOLLOW_UP_GENERATION_NODE: consts.FOLLOW_UP_GENERATION_NODE,
            consts.DIAGNOSIS_GENERATOR_NODE: consts.DIAGNOSIS_GENERATOR_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.DIAGNOSIS_GENERATOR_NODE,
        edges.route_after_generation,
        {
            consts.UNIVERSAL_FALLBACK_NODE: consts.UNIVERSAL_FALLBACK_NODE,
            consts.SAFETY_CRITIC_NODE: consts.SAFETY_CRITIC_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.FOLLOW_UP_GENERATION_NODE,
        edges.route_after_generation,
        {
            consts.UNIVERSAL_FALLBACK_NODE: consts.UNIVERSAL_FALLBACK_NODE,
            consts.SAFETY_CRITIC_NODE: consts.SAFETY_CRITIC_NODE,
        },
    )

    workflow.add_conditional_edges(
        consts.SAFETY_CRITIC_NODE,
        edges.route_after_critic,
        {
            END: END,
            consts.UNIVERSAL_FALLBACK_NODE: consts.UNIVERSAL_FALLBACK_NODE,
            consts.FOLLOW_UP_GENERATION_NODE: consts.FOLLOW_UP_GENERATION_NODE,
            consts.DIAGNOSIS_GENERATOR_NODE: consts.DIAGNOSIS_GENERATOR_NODE,
        },
    )

    workflow.add_edge(consts.GENERAL_CHAT_NODE, END)
    workflow.add_edge(consts.UNIVERSAL_FALLBACK_NODE, END)

    return workflow



uncompiled_workflow = build_uncompiled_graph()
