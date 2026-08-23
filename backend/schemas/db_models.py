"""schemas/models.py: SQLAlchemy 2.0 ORM models for PostgreSQL (Supabase)."""

import uuid
from typing import Any

from database.session import Base
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column


class DiseaseTreatment(Base):
    """Stores agronomic treatment guides and weather constraints."""

    __tablename__ = "disease_treatments"

    disease_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
        comment="Primary Key, linked to vector search metadata",
    )

    disease_name: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        comment="Name of the disease, e.g., 'Rice Leaf Blast'",
    )

    treatment_guide_doc: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="The master Markdown file containing ALL chemicals, organic options, and cultural practices",
    )

    weather_constraints: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        comment="Simple JSON,contains weather constraints for the disease.",
    )

    def __repr__(self) -> str:
        return f"<DiseaseTreatment(name={self.disease_name!r}, id={self.disease_id})>"
