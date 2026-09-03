"""api/voice.py: On-demand streaming endpoint for historical chat playback."""

import logging

from fastapi import APIRouter, HTTPException, Response
from schemas.api_models import VoiceReplayRequest
from services.voice_output import generate_speech_bytes

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/voice/stream", response_class=Response)
async def stream_replay_audio(request: VoiceReplayRequest):
    """
    Streams live MP3 bytes directly for historical message playback
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text cannot be empty.")

    try:
        audio_bytes = await generate_speech_bytes(request.text, request.language_code)

        if not audio_bytes:
            raise HTTPException(status_code=500, detail="Failed to synthesize speech.")

        return Response(content=audio_bytes, media_type="audio/mpeg")

    except Exception:
        logger.exception("Voice synthesis failed during replay.")
        raise HTTPException(
            status_code=500, detail="Internal server error during audio generation."
        )
