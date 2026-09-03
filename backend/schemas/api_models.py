"""schemas/api_models.py: Pydantic schemas for API requests and responses."""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    user_id: str = Field(..., description="UUID of the user")
    thread_id: str = Field(..., description="Unique session ID for LangGraph checkpointer")
    audio_base64: str = Field("", description="Microphone recording in Base64")
    language_code: str = Field("en", description="Target language code (e.g., 'kn', 'en')")
    images: list[str] = Field(default_factory=list, description="List of base64 crop photos")

class ChatResponse(BaseModel):
    thread_id: str
    ai_response_text: str
    ai_response_audio_base64: str  
    is_flow_complete: bool

class VoiceReplayRequest(BaseModel):
    text: str = Field(..., description="The message text to convert to speech")
    language_code: str = Field(
        "en", description="Target language code (e.g., 'kn', 'en')"
    )
