"""api/chat.py: Unified multimodal voice chat endpoint."""

import logging

from ai_core import constants as consts
from ai_core.graph import uncompiled_workflow
from database.checkpointer import get_postgres_checkpointer
from database.postgres_db import backfill_cycle_id
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from schemas.api_models import ChatRequest, ChatResponse
from services.background_tasks import (
    process_and_save_chat,
    process_and_save_medical_log,
)
from services.localization import translate_english_to_native
from services.voice_input import native_to_english_text, speech_to_native_text
from services.voice_output import generate_speech_base64

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse, status_code=status.HTTP_200_OK)
async def chat_endpoint(request: ChatRequest, background_tasks: BackgroundTasks):
    config = {"configurable": {"thread_id": request.thread_id}}
    target_lang = request.language_code

    # INBOUND VOICE PROCESSING (Sarvam)

    user_native = ""
    if request.audio_base64.strip():
        user_native = await speech_to_native_text(request.audio_base64)
        if not user_native:
            raise HTTPException(status_code=400, detail="Voice recognition failed.")

    # Translate Native -> English for LangGraph
    user_english = ""
    if user_native:
        user_english = await native_to_english_text(user_native, f"{target_lang}-IN")

    # LANGGRAPH WORKFLOW EXECUTION
    async with get_postgres_checkpointer() as checkpointer:
        app = uncompiled_workflow.compile(
            checkpointer=checkpointer, interrupt_before=[consts.HUMAN_INPUT_NODE]
        )
        state = await app.aget_state(config)
        is_resuming = bool(state.next)

        if is_resuming:
            # Resuming graph from a Human-In-The-Loop pause
            payload = {"have_question": False}
            if user_english:
                payload["clarification_answer"] = user_english
            if request.images:
                payload["new_uploaded_images"] = request.images

            await app.aupdate_state(config, payload)
            await app.ainvoke(None, config)
        else:
            # Starting fresh graph execution
            await app.ainvoke(
                {
                    "user_id": request.user_id,
                    "user_text": user_english,
                    "images": request.images,
                },
                config,
            )

        final_state = await app.aget_state(config)
        is_complete = len(final_state.next) == 0

        # Extract the English response from the graph's state
        english_output = (
            final_state.values.get("final_diagnosis")
            if is_complete
            else final_state.values.get("clarifying_question")
        )

        if not english_output:
            english_output = "I am processing your request, please wait."

    # LOCALIZATION & VOICE OUTPUT
    native_ai_text = await translate_english_to_native(english_output, target_lang)
    audio_base64 = await generate_speech_base64(native_ai_text, target_lang)

    # ASYNC BACKGROUND WORKERS (DB Logging & Supabase)
    current_cycle_id = final_state.values.get("cycle_id")

    # ALWAYS Save User Input instantly
    background_tasks.add_task(
        process_and_save_chat,
        user_id=request.user_id,
        thread_id=request.thread_id,
        cycle_id=current_cycle_id,
        role="user",
        category="CLARIFICATION" if is_resuming else "INITIAL_QUERY",
        language_code=target_lang,
        display_content=user_native,
        english_content=user_english,
        images_base64=request.images,
    )

    # ALWAYS Save AI Response instantly
    background_tasks.add_task(
        process_and_save_chat,
        user_id=request.user_id,
        thread_id=request.thread_id,
        cycle_id=current_cycle_id,
        role="assistant",
        category="FINAL_DIAGNOSIS" if is_complete else "INTERMEDIATE_QUESTION",
        language_code=target_lang,
        display_content=native_ai_text,
        english_content=english_output,
        images_base64=[],
    )

    # Backfill early history if cycle_id now exists
    if current_cycle_id:
        background_tasks.add_task(
            backfill_cycle_id, request.thread_id, current_cycle_id
        )

    # Summarize & save medical log ONLY if finalized
    is_approved = final_state.values.get("is_approved", False)

    if is_complete and current_cycle_id and is_approved:
        background_tasks.add_task(
            process_and_save_medical_log,
            cycle_id=str(current_cycle_id),
            crop_age_days=final_state.values.get("crop_age_days", 0),
            english_diagnosis=english_output,
        )
    elif is_complete:
        logger.warning(
            f"Thread {request.thread_id} completed, but is_approved is False. "
            f"Skipping medical log (likely a fatal error or aborted flow)."
        )

    # FRONTEND RESPONSE
    return ChatResponse(
        thread_id=request.thread_id,
        ai_response_text=native_ai_text,
        ai_response_audio_base64=audio_base64,
        is_flow_complete=is_complete,
    )
