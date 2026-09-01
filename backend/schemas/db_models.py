"""schemas/models.py: SQLAlchemy ORM models for PostgreSQL (Supabase)."""

import uuid
from datetime import datetime, timezone
from typing import Any

from database.session import Base
from sqlalchemy import (
    ARRAY,
    CheckConstraint,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship


class User(Base):
    __tablename__ = "users"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    mobile_number = Column(String(15), unique=True, nullable=True)
    farm_latitude = Column(Float, nullable=True)
    farm_longitude = Column(Float, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    cycles = relationship(
        "CropCycle", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, mobile_number={self.mobile_number!r})>"


class CropCycle(Base):
    __tablename__ = "crop_cycles"

    cycle_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False,
    )
    planting_date = Column(Date, nullable=False)
    expected_harvest_date = Column(Date, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    user = relationship("User", back_populates="cycles")
    medical_logs = relationship(
        "CropMedicalLog", back_populates="cycle", cascade="all, delete-orphan"
    )
    chat_messages = relationship(
        "ChatMessage", back_populates="cycle", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<CropCycle(id={self.cycle_id}, user_id={self.user_id})>"


class CropMedicalLog(Base):
    __tablename__ = "crop_medical_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_cycles.cycle_id", ondelete="CASCADE"),
        nullable=False,
    )
    event_date = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    crop_age_days = Column(Integer, nullable=False)
    event_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)

    # Relationships
    cycle = relationship("CropCycle", back_populates="medical_logs")

    def __repr__(self) -> str:
        return f"<CropMedicalLog(id={self.log_id}, cycle_id={self.cycle_id})>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id = Column(
        UUID(as_uuid=True),
        ForeignKey("crop_cycles.cycle_id", ondelete="CASCADE"),
        nullable=False,
    )
    role = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False, default="INITIAL_QUERY")
    language_code = Column(String(10), nullable=False, default="en")
    display_content = Column(Text, nullable=False)
    english_content = Column(Text, nullable=False)
    image_urls = Column(ARRAY(String), default=list)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint(role.in_(["user", "assistant"]), name="valid_role"),
    )

    # Relationships
    cycle = relationship("CropCycle", back_populates="chat_messages")

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.message_id}, cycle_id={self.cycle_id}, role={self.role!r}, category={self.category!r})>"


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
