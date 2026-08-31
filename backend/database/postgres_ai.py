"""database/postgres_ai.py: Fetches treatment guides and AI context from PostgreSQL."""

import logging
import uuid
from datetime import datetime, timezone
from typing import Any

from database.session import SessionLocal
from schemas.db_models import (
    ChatMessage,
    CropCycle,
    CropMedicalLog,
    DiseaseTreatment,
    User,
)
from sqlalchemy import desc, select

logger = logging.getLogger(__name__)


async def get_treatment_by_disease_id(disease_id: str) -> dict[str, Any] | None:
    """
    Fetches exact treatment guides and weather constraints from the relational database.
    Used by the graph after the AI confidently identifies the specific disease.
    """
    async with SessionLocal() as session:
        try:
            disease_uuid = uuid.UUID(disease_id)
            stmt = select(DiseaseTreatment).where(
                DiseaseTreatment.disease_id == disease_uuid
            )
            result = await session.execute(stmt)
            record = result.scalar_one_or_none()

            if not record:
                return None

            return {
                "disease_id": str(record.disease_id),
                "disease_name": record.disease_name,
                "treatment_guide": record.treatment_guide_doc,
                "weather_constraints": record.weather_constraints,
            }

        except Exception:
            logger.exception("Relational treatment fetch failed")
            return None


async def get_active_crop_context(user_id: str) -> dict[str, Any] | None:
    """
    Fetches the active crop cycle and the farm's GPS coordinates.
    Checks if today's date is before or equal to the expected_harvest_date.
    """
    async with SessionLocal() as session:
        try:
            user_uuid = uuid.UUID(user_id)
            today = datetime.now(timezone.utc).date()

            stmt = (
                select(CropCycle, User.farm_latitude, User.farm_longitude)
                .join(User, User.user_id == CropCycle.user_id)
                .where(CropCycle.user_id == user_uuid)
                .where(CropCycle.expected_harvest_date >= today)
                .order_by(desc(CropCycle.created_at))
                .limit(1)
            )

            result = await session.execute(stmt)
            row = result.first()

            if not row:
                return None

            cycle, lat, lon = row
            return {
                "cycle_id": str(cycle.cycle_id),
                "planting_date": cycle.planting_date.isoformat(),
                "farm_latitude": lat,
                "farm_longitude": lon,
            }

        except Exception:
            logger.exception(f"Failed to fetch active crop context for user {user_id}")
            return None


async def get_recent_chat_history(
    cycle_id: str, limit: int = 6
) -> list[dict[str, str]]:
    """
    Fetches the last N messages for the active cycle and formats them
     into a single readable string for LLM prompts.
    """
    async with SessionLocal() as session:
        try:
            cycle_uuid = uuid.UUID(cycle_id)

            stmt = (
                select(ChatMessage)
                .where(ChatMessage.cycle_id == cycle_uuid)
                .order_by(desc(ChatMessage.created_at))
                .limit(limit)
            )

            result = await session.execute(stmt)
            messages = result.scalars().all()

            if not messages:
                return "No previous history."

            formatted_history = "\n".join(
                [
                    f"{msg.role.capitalize()}: {msg.content}"
                    for msg in reversed(messages)
                ]
            )
            return formatted_history

        except Exception:
            logger.exception(
                f"Failed to fetch short-term chat history for cycle {cycle_id}"
            )
            return "No previous history."


async def get_medical_timeline(cycle_id: str) -> str | None:
    """
    Fetches the log of previous events and formats it into a
    highly condensed string for the Generation Node context window.
    """
    async with SessionLocal() as session:
        try:
            cycle_uuid = uuid.UUID(cycle_id)

            stmt = (
                select(CropMedicalLog)
                .where(CropMedicalLog.cycle_id == cycle_uuid)
                .order_by(CropMedicalLog.event_date.asc())
            )

            result = await session.execute(stmt)
            logs = result.scalars().all()

            if not logs:
                return None

            timeline_str = "### Crop Medical Log Timeline\n"
            for log in logs:
                date_str = log.event_date.strftime("%Y-%m-%d")
                timeline_str += (
                    f"- [{date_str} | Day {log.crop_age_days}] "
                    f"{log.event_type.upper()}: {log.description}\n"
                )

            return timeline_str

        except Exception:
            logger.exception(f"Failed to fetch medical timeline for cycle {cycle_id}")
            return None
