"""services/service_llms.py: Dedicated LLM instances for external services (translation, summarization)."""

from typing import Literal

from config.settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

API_KEYS = [
    settings.GOOGLE_API_KEY_1,
    settings.GOOGLE_API_KEY_2,
    settings.GOOGLE_API_KEY_3,
]


def build_service_llm_pool(
    model_preference_list: list[str], temperature: float, key_shift: int = 0
) -> ChatGoogleGenerativeAI:
    """
    Builds a resilient LLM chain using key_shift to avoid rate-limit collisions
    with the main LangGraph AI Core execution.
    """
    shifted_keys = API_KEYS[key_shift:] + API_KEYS[:key_shift]

    llms = []

    for model_name in model_preference_list:
        for key in shifted_keys:
            if key:
                llms.append(
                    ChatGoogleGenerativeAI(
                        model=model_name,
                        temperature=temperature,
                        google_api_key=key,
                        max_retries=0,
                    )
                )

    if not llms:
        raise ValueError("No valid Google API keys found for Service LLMs.")

    primary_llm = llms[0]
    fallback_llms = llms[1:]

    return primary_llm.with_fallbacks(fallback_llms)


# 1. TRANSLATION LLM
translator_llm = build_service_llm_pool(
    model_preference_list=[
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
    ],
    temperature=0.1,
    key_shift=2,
)


# 2. BACKGROUND / UTILITY LLM

class MedicalLogSummarySchema(BaseModel):
    event_type: Literal["DISEASE", "PEST", "NUTRIENT", "ADVISORY"] = Field(
        description="The category of the agricultural event."
    )
    description: str = Field(
        description="A concise summary of the diagnosis in a maximum of 15 words."
    )


background_llm = build_service_llm_pool(
    model_preference_list=[
        "gemma-4-26b-a4b-it",
        "gemma-4-31b-it",
    ],
    temperature=0.0,
    key_shift=0,
)

structured_medical_llm = background_llm.with_structured_output(MedicalLogSummarySchema)
