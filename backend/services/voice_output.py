"""services/voice_output.py: Edge-TTS audio generation in memory with cloud-safe female TTS fallback."""

import base64
import logging
import re

import edge_tts
import httpx

logger = logging.getLogger(__name__)

# Female neural voices for Kannada and Indian English
VOICE_MAPPING = {
    "kn": "kn-IN-SapnaNeural",
    "en": "en-IN-NeerjaNeural",
}

# Google TTS language codes (uses female voice for both kn and en-IN)
GOOGLE_TTS_LANG_MAPPING = {
    "kn": "kn",
    "en": "en-IN",
}

MAX_GOOGLE_TTS_CHARS = 180


def _split_text_for_tts(text: str, max_chars: int = MAX_GOOGLE_TTS_CHARS) -> list[str]:
    """
    Cleans markdown formatting and splits text into natural sentence chunks
    under `max_chars` so Google TTS can synthesize arbitrarily long responses.
    """
    cleaned = re.sub(r"[*_#`~>]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return []

    sentences = re.split(r"(?<=[.!?।])\s+", cleaned)
    chunks: list[str] = []
    current = ""

    for sentence in sentences:
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            words = sentence.split(" ")
            sub = ""
            for word in words:
                if len(sub) + len(word) + 1 <= max_chars:
                    sub = f"{sub} {word}".strip()
                else:
                    if sub:
                        chunks.append(sub)
                    sub = word[:max_chars]
            if sub:
                chunks.append(sub)
        elif len(current) + len(sentence) + 1 <= max_chars:
            current = f"{current} {sentence}".strip()
        else:
            if current:
                chunks.append(current.strip())
            current = sentence

    if current:
        chunks.append(current.strip())

    return chunks


async def _generate_google_tts_fallback(text: str, language_code: str = "en") -> bytes:
    """
    Fallback female-voice TTS over standard HTTPS (works on Render/cloud datacenter IPs
    where Microsoft blocks edge-tts WebSocket connections).
    """
    tl = GOOGLE_TTS_LANG_MAPPING.get(language_code, "en-IN")
    chunks = _split_text_for_tts(text)
    if not chunks:
        return b""

    url = "https://translate.google.com/translate_tts"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
    }

    buffer = bytearray()
    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for chunk in chunks:
            params = {
                "ie": "UTF-8",
                "client": "tw-ob",
                "tl": tl,
                "q": chunk,
            }
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            if response.content:
                buffer.extend(response.content)

    return bytes(buffer)


# Generates MP3 audio bytes from the given text using Edge TTS with automatic HTTPS fallback.
async def generate_speech_bytes(text: str, language_code: str = "en") -> bytes:
    """Streams audio into a RAM buffer as MP3 bytes using female voices."""
    if not text.strip():
        return b""

    voice = VOICE_MAPPING.get(language_code, "en-IN-NeerjaNeural")
    try:
        communicate = edge_tts.Communicate(text, voice)
        buffer = bytearray()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.extend(chunk["data"])

        if buffer:
            return bytes(buffer)
    except Exception as err:
        logger.warning(
            f"Edge-TTS blocked or failed ({err!s}). Switching to HTTPS female TTS fallback."
        )

    try:
        return await _generate_google_tts_fallback(text, language_code)
    except Exception:
        logger.exception("Both Edge-TTS and HTTPS fallback TTS failed.")
        return b""


# Converts generated MP3 audio bytes into a base64-encoded string.
async def generate_speech_base64(text: str, language_code: str = "kn") -> str:
    """Directly returns base64 MP3 for immediate playback in the /chat response."""
    audio_bytes = await generate_speech_bytes(text, language_code)

    if not audio_bytes:
        return ""

    return base64.b64encode(audio_bytes).decode("utf-8")
