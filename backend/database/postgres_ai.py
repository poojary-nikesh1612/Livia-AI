"""database/postgres_ai.py: Fetches treatment guides."""

import logging
import uuid
from typing import Any

from schemas.db_models import DiseaseTreatment
from sqlalchemy import select

from database.session import SessionLocal

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
