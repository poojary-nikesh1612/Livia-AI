"""services/voice_output.py: Edge-TTS audio generation in memory."""

import base64
import logging

import edge_tts

logger = logging.getLogger(__name__)

VOICE_MAPPING = {
    "kn": "kn-IN-SapnaNeural",
    "en": "en-IN-NeerjaNeural",
}


# Generates MP3 audio bytes from the given text using Edge TTS.
async def generate_speech_bytes(text: str, language_code: str = "en") -> bytes:
    """Streams audio into a RAM buffer as MP3 bytes."""
    if not text.strip():
        return b""

    voice = VOICE_MAPPING.get(language_code, "en-IN-NeerjaNeural")
    try:
        communicate = edge_tts.Communicate(text, voice)
        buffer = bytearray()

        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.extend(chunk["data"])

        return bytes(buffer)
    except Exception:
        logger.exception("Edge-TTS synthesis error.")
        return b""


# Converts generated MP3 audio bytes into a base64-encoded string.
async def generate_speech_base64(text: str, language_code: str = "kn") -> str:
    """Directly returns base64 MP3 for immediate playback in the /chat response."""
    audio_bytes = await generate_speech_bytes(text, language_code)

    if not audio_bytes:
        return ""

    return base64.b64encode(audio_bytes).decode("utf-8")
