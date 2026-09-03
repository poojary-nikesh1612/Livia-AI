"""main.py: Application entry point for Livia-AI Backend."""

from api import chat, voice
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Livia-AI Agricultural Advisory Backend",
    description="Multimodal voice-first backend for crop diagnosis and advisory.",
    version="1.0.0",
)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers
app.include_router(chat.router, prefix="/api/v1", tags=["Chat"])
app.include_router(voice.router, prefix="/api/v1", tags=["Voice"])


@app.get("/health", tags=["System"])
async def health_check():
    """Standard health check endpoint for server monitoring."""
    return {"status": "healthy"}
