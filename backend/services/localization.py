"""services/localization.py: Translates English graph outputs to Native text."""

import logging

from services.dictionaries import AGRI_GLOSSARY, EXACT_STRING_TRANSLATIONS
from services.llm_translator import translator_llm

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
   - When any crop disease name appears from the glossary, write the native term followed immediately by its English name in colloquial phrasing.
     For Kannada ('kn'), format it exactly like this:
     "[Native Name] ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ \"[English Name]\" ಅಂತ ಕರೀತಾರೆ"
     Example: "ಬೆಂಕಿ ರೋಗ ಇಂಗ್ಲಿಷ್‌ನಲ್ಲಿ \"Rice Blast\" ಅಂತ ಕರೀತಾರೆ"
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
