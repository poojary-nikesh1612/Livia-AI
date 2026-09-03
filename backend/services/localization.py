"""services/localization.py: Translates English graph outputs to Native text."""

import logging

from services.dictionaries import AGRI_GLOSSARY, EXACT_STRING_TRANSLATIONS
from services.service_llms import translator_llm

logger = logging.getLogger(__name__)


async def translate_english_to_native(
    english_text: str, target_lang: str = "kn"
) -> str:
    """
    Translates graph output into native language seamlessly:
    1. Exact string lookup.
    2. Dynamic Gemini LLM translation with glossary enforcement.
    """
    if target_lang == "en" or not english_text.strip():
        return english_text

    # Exact string lookup (Static Graph Outputs)
    normalized_text = english_text.strip()
    lang_dict = EXACT_STRING_TRANSLATIONS.get(target_lang, {})

    if normalized_text in lang_dict:
        logger.info("⚡ Translation Cache Hit: Exact string match found.")
        return lang_dict[normalized_text]

    # Dynamic translation using LLM
    logger.info(
        f"🧠 Translation Cache Miss: Translating dynamic output using LLM {target_lang}."
    )

    glossary = AGRI_GLOSSARY.get(target_lang, {})
    glossary_rules = "\n".join(
        [f"- {eng} -> {native}" for eng, native in glossary.items()]
    )

    prompt = f"""You are an agricultural translation specialist for Indian farmers.
Translate the following English diagnostic note into language code '{target_lang}'.

MANDATORY RULES:
1. TERMINOLOGY & DISEASE NAMING:
   - FIRST OCCURRENCE: When a crop disease from the glossary is mentioned for the very first time, integrate both the native and English names smoothly into a natural, conversational sentence (e.g., "Your crop is affected by [Native Name], which is known as [English Name] in English.").
   - NO PARENTHESES: Do NOT use parentheses () or brackets [] to insert the English name. The sentence must flow naturally.
   - SUBSEQUENT OCCURRENCES: For all later mentions of the same disease in the text, use ONLY the native name. Do not repeat the English name.
   - Reference Glossary:
{glossary_rules}

2. CHEMICALS & DOSAGES:
   - Keep chemical names, active ingredients, and exact numerical measurements/dosages (e.g., ml/L, g/acre, 50 EC) perfectly preserved and clearly readable.

3. TONE & STYLE:
   - Use simple, respectful, conversational language suited for a rural farmer.
   - Do NOT use difficult Sanskritized or academic words.

English text:
{english_text}

Output ONLY the translated text without commentary."""

    try:
        response = await translator_llm.ainvoke(prompt)
        return response.content[-1]['text']
    except Exception:
        logger.exception("Gemini translation failed.")
        return english_text  
