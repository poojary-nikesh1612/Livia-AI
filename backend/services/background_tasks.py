"""services/background_tasks.py: Orchestrates async background operations."""

import json
import logging
import uuid

from database.postgres_db import insert_medical_log, save_chat_message

from services.service_llms import structured_medical_llm
from services.storage import upload_base64_images

logger = logging.getLogger(__name__)


async def process_and_save_chat(
    user_id : str,
    thread_id: str,
    cycle_id: str,
    role: str,
    category: str,
    language_code: str,
    display_content: str,
    english_content: str,
    images_base64: list[str] | None = None,
):
    """
    Background worker: Uploads images to Supabase, then saves the chat message to PostgreSQL.
    """
    image_urls = []
    if images_base64:
        logger.info(f"Uploading {len(images_base64)} images to Supabase...")
        image_urls = await upload_base64_images(images_base64)

    await save_chat_message(
        user_id=uuid.UUID(user_id),
        thread_id=thread_id,
        cycle_id=uuid.UUID(cycle_id),
        role=role,
        category=category,
        language_code=language_code,
        display_content=display_content,
        english_content=english_content,
        image_urls=image_urls,
    )


async def process_and_save_medical_log(
    cycle_id: str, crop_age_days: int, english_diagnosis: str
):
    """
    Background worker: Summarizes the final diagnosis using the Gemma LLM,
    then saves the condensed timeline log to PostgreSQL.
    """
    prompt = f"""
        You are an AI assistant helping to condense agricultural diagnostic logs.
        Summarize the following diagnosis into a strict maximum of 15 words, and assign the appropriate category.
        
        Diagnosis to summarize:
        "{english_diagnosis}"
        """

    try:
        # LLM call
        summary = await structured_medical_llm.ainvoke(prompt)

        # Save to the DB
        await insert_medical_log(
            cycle_id=uuid.UUID(cycle_id),
            crop_age_days=crop_age_days,
            event_type=summary.event_type,
            description=summary.description,
        )

    except json.JSONDecodeError:
        logger.error("Gemma returned invalid JSON for medical log summary.")
        # Fallback save if LLM fails
        await insert_medical_log(
            cycle_id=uuid.UUID(cycle_id),
            crop_age_days=crop_age_days,
            event_type="ADVISORY",
            description="Diagnostic cycle completed.",
        )
    except Exception:
        logger.exception("Failed to process medical log.")
