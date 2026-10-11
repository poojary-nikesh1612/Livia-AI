"""API endpoint for retrieving a user's chat history."""

import logging
import uuid

from database.postgres_db import get_chat_messages
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/chat/history")
async def get_user_chat_history(user_id: uuid.UUID):
    """Return all messages for a user in chronological order."""
    try:
        return await get_chat_messages(user_id)
    except Exception as exc:
        logger.exception("Failed to fetch chat history for user %s", user_id)
        raise HTTPException(
            status_code=500, detail="Failed to retrieve chat history."
        ) from exc
