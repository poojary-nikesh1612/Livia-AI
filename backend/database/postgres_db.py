"""database/postgres_ai.py: Handles general database operations."""

import logging
import uuid

from database.session import SessionLocal
from schemas.db_models import ChatMessage, CropMedicalLog
from sqlalchemy import update

logger = logging.getLogger(__name__)


# Save a chat message.
async def save_chat_message(
    user_id: uuid.UUID | None,
    thread_id: str,
    cycle_id: uuid.UUID | None,
    role: str,
    category: str,
    language_code: str,
    display_content: str,
    english_content: str,
    image_urls: list[str] | None = None,
) -> uuid.UUID | None:
    """
    Saves a message to the chat_messages table.
    """
    if image_urls is None:
        image_urls = []

    try:

        async with SessionLocal() as db:
            new_message = ChatMessage(
                user_id=user_id,
                thread_id=thread_id,
                cycle_id=cycle_id,
                role=role,
                category=category,
                language_code=language_code,
                display_content=display_content,
                english_content=english_content,
                image_urls=image_urls,
            )

            db.add(new_message)
            await db.commit()

    except Exception:
        logger.exception("Error while saving chat message")

# Updating cycle_id for pre-cycle messages
async def backfill_cycle_id( thread_id: str,
    cycle_id: uuid.UUID):
    """Links all early 'pre-cycle' messages to the new cycle_id once it is available."""
    try:
        async with SessionLocal() as db:
            stmt = (
                update(ChatMessage)
                .where(ChatMessage.thread_id == thread_id)
                .where(ChatMessage.cycle_id == None)
                .values(cycle_id=cycle_id)
            )
            await db.execute(stmt)
            await db.commit()
            logger.info(
                f"🔗 Linked previous messages in thread {thread_id} to cycle {cycle_id}"
            )
    except Exception:
        logger.exception("Error backfilling cycle_id")


# Save a medical log
async def insert_medical_log(
    cycle_id: str | uuid.UUID, crop_age_days: int, event_type: str, description: str
) -> uuid.UUID | None:
    """
    Inserts a condensed diagnostic log event into the crop_medical_logs timeline.
    """
    try:
        valid_cycle_id = (
            uuid.UUID(str(cycle_id)) if isinstance(cycle_id, str) else cycle_id
        )

        async with SessionLocal() as db:
            new_log = CropMedicalLog(
                cycle_id=valid_cycle_id,
                crop_age_days=crop_age_days,
                event_type=event_type.upper(),
                description=description,
            )

            db.add(new_log)
            await db.commit()

    except Exception:
        logger.exception("Error while inserting medical log")
        logger.exception("Error while inserting medical log")
