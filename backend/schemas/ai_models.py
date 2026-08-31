"""schemas/ai_models.py: Pydantic schemas for LLM structured outputs and shared types."""

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


# Enum for supported crop growth stages
class CropStage(StrEnum):
    """Supported growth stages for paddy crops."""

    SEEDLING = "seedling"
    TILLERING = "tillering"
    PANICLE_INITIATION = "panicle_initiation"
    BOOTING = "booting"
    HEADING = "heading"
    FLOWERING = "flowering"
    MILKY = "milky"
    MATURITY = "maturity"


# output model for crop age extraction llm
class CropAgeExtraction(BaseModel):
    is_understood: bool = Field(
        description="True if the user's text contains a recognizable time period or date."
    )
    age_in_days: int | None = Field(
        description="The extracted age in days. Examples: 'a month' = 30, '3 weeks' = 21, '45 days' = 45.",
        default=None,
    )


# Output model for route decision llm
class RouteDecision(BaseModel):
    destination: Literal[
        "general_chat_node",
        "follow_up_generation_node",
        "request_image_node",
        "vision_node",
    ] = Field(description="The exact route destination based on the intent rules.")
    reasoning: str = Field(
        description="A brief 1-sentence explanation of why this route was chosen."
    )


# Output model for vision llm
class ImageAnalysis(BaseModel):
    is_usable: bool = Field(
        description="Evaluate clarity and relevance. TRUE: Clear, identifiable paddy/rice plant. FALSE: Blurry, dark, too distant, or non-paddy subjects (e.g., animals, machinery, wheat)."
    )
    visual_features: str = Field(
        description="IF USABLE: Extract exact paddy pathology symptoms. Detail leaf discoloration (e.g., yellow tips, brown streaks), lesion shapes (e.g., diamond/spindle spots), stem rotting, or visible pests. State observable facts only. IF UNUSABLE: Provide a 2-5 word rejection reason (e.g., 'Too blurry', 'Not a plant')."
    )

# Output model for vision llm as a batch
class BatchVisionResult(BaseModel):
    evaluations: list[ImageAnalysis] = Field(
        description="A strictly ordered list containing exactly one evaluation object per input image."
    )

# Output model for symptom alignment llm
class SymptomAlignment(BaseModel):
    is_aligned: bool = Field(
        description="True if the combined User Text, Visual Text, AND Clarification History form a unified, clear picture. If the History resolves an initial mismatch between the user and visual texts, this MUST be True."
    )
    clarifying_question: str | None = Field(
        description="If is_aligned is False (due to an unresolved contradiction NOT answered in the History), write ONE specific question for the farmer to resolve it. If True, return None."
    )
    aligned_symptom_profile: str | None = Field(
        description="If is_aligned is True, write a unified, highly descriptive paragraph combining the grounded facts. If False, return None."
    )

# Output model for investigative question chain
class InvestigativeQuestionOutput(BaseModel):
    clarifying_question: str = Field(
        description="A single, farmer-friendly open-ended question to gather missing diagnostic details."
    )

# Output model for symptom update chain
class SymptomRefinementOutput(BaseModel):
    updated_symptom_profile: str = Field(
        description=(
            "The comprehensive, updated symptom profile written in objective, "
            "standardized agronomic terms optimized for semantic vector retrieval."
        )
    )

# Output model for safety critic chain
class CriticEvaluation(BaseModel):
    is_approved: bool = Field(
        description="True ONLY if the draft is safe, grounded, and easily understood by an everyday farmer. False if it fails ANY check."
    )
    critic_feedback: str = Field(
        description="If rejected, write a 1-2 sentence instruction on what MUST be changed. If approved, write 'None'."
    )