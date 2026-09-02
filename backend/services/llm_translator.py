"""services/llm_translator.py: Dedicated LLM instance for outbound localization."""

from config.settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI

KEYS = [
    settings.GOOGLE_API_KEY_1,
    settings.GOOGLE_API_KEY_2,
    settings.GOOGLE_API_KEY_3,
]


def build_translation_llm() -> ChatGoogleGenerativeAI:
    """
    A LLM chain specifically for translation tasks.
    """
    llms = []

    preferred_models = [
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-3.5-flash",
    ]

    # Create an LLM instance for every combination of model + key
    for model_name in preferred_models:
        for key in KEYS:
            if key:
                llms.append(
                    ChatGoogleGenerativeAI(
                        model=model_name,
                        temperature=0.1,
                        google_api_key=key,
                        max_retries=0,
                    )
                )

    if not llms:
        raise ValueError("No valid Google API keys found for Translation LLM.")

    primary_llm = llms[0]
    fallback_llms = llms[1:]

    return primary_llm.with_fallbacks(fallback_llms)


translator_llm = build_translation_llm()
