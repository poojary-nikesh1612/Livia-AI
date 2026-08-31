"""ai_core/llm_config.py: Tiered, multi-key factory for Google Gemini."""

from config.settings import settings
from langchain_google_genai import ChatGoogleGenerativeAI

API_KEYS = [
    settings.GOOGLE_API_KEY_1,
    settings.GOOGLE_API_KEY_2,
    settings.GOOGLE_API_KEY_3,
]

def build_llm_pool(
    model_preference_list: list[str], 
    temperature: float,
    key_shift: int = 0
) -> ChatGoogleGenerativeAI:
    """
    Builds a resilient LLM chain by cross-multiplying preferred models with all API keys.
    Uses `key_shift` to rotate which API key is used first to balance the load.
    """
    # Shift the array of keys so different pools start on different keys!
    # If key_shift is 1: [Key 2, Key 3, Key 1]
    shifted_keys = API_KEYS[key_shift:] + API_KEYS[:key_shift]
    
    llms = []

    for model_name in model_preference_list:
        for key in shifted_keys:
            llms.append(
                ChatGoogleGenerativeAI(
                    model=model_name,
                    temperature=temperature,
                    google_api_key=key,
                    max_retries=0,
                )
            )

    primary_llm = llms[0]
    fallback_llms = llms[1:]

    # Returns a chain that tries primary, then cascades through the fallbacks on failure
    return primary_llm.with_fallbacks(fallback_llms)



# 1. REASONING LLM 
reasoning_llm = build_llm_pool(
    model_preference_list=[
        "gemma-4-31b-it",
        "gemini-3.7-flash",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-3-flash-preview",
        "gemini-3.5-flash-lite",
    ],
    temperature=0.3,
    key_shift=0  
)



# 2. LIGHTWEIGHT LLM 
lightweight_llm = build_llm_pool(
    model_preference_list=[
        "gemma-4-26b-a4b-it",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
    ],
    temperature=0.0, 
    key_shift=1  
)


# 3. VISION LLM (Image feature extraction)
vision_llm = build_llm_pool(
    model_preference_list=[
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-3-flash-preview",
        "gemini-3.5-flash-lite",
    ],
    temperature=0.1,
    key_shift=2  
)
# print(ai_msg.content[-1]['text'])
