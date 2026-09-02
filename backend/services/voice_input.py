"""services/voice_input.py: Handles inbound farmer audio and text."""

import base64
import logging

import httpx
from config.settings import settings

logger = logging.getLogger(__name__)

SARVAM_API_KEY = getattr(settings, "SARVAM_API_KEY", "").strip()

# Converts audio to navtive text
async def speech_to_native_text(audio_base64: str) -> str:
    """Transcribes farmer's audio into native script using Saaras v3."""
    if not audio_base64:
        return ""
        
    if not SARVAM_API_KEY:
        logger.error("SARVAM_API_KEY is missing from environment variables.")
        return ""

    try:
        audio_bytes = base64.b64decode(audio_base64)
        url = "https://api.sarvam.ai/speech-to-text"
        files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
        data = {"model": "saaras:v3", "mode": "transcribe"}
        headers = {"api-subscription-key": SARVAM_API_KEY}

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, headers=headers, files=files, data=data)
            res.raise_for_status()
            return res.json().get("transcript", "")
            
    except Exception:
        logger.exception("Sarvam STT extraction error.")
        return ""

# Translates native text to english
async def native_to_english_text(native_text: str, source_lang_code: str = "kn-IN") -> str:
    """Translates incoming native text to English using Mayura v1."""
    if not native_text.strip() or source_lang_code.startswith("en"):
        return native_text
        
    if not SARVAM_API_KEY:
        return native_text

    try:
        url = "https://api.sarvam.ai/translate"
        payload = {
            "input": native_text,
            "source_language_code": source_lang_code,
            "target_language_code": "en-IN",
            "model": "mayura:v1"
        }
        headers = {"api-subscription-key": SARVAM_API_KEY}

        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, headers=headers, json=payload)
            res.raise_for_status()
            return res.json().get("translated_text", native_text)
            
    except Exception:
        logger.exception("Sarvam inbound translation error.")
        return native_text       