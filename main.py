"""
AI Shorts Studio - AI Worker Main Entry Point.

This is the separate AI Worker service that handles:
- Text generation (Ollama)
- Image generation (Diffusers / Stable Diffusion)
- Video generation (Wan / LTX-Video / CogVideoX)
- Voice generation (Piper / Kokoro)
- STT / Subtitles (Whisper)
- Music selection and generation
- Automatic video editing and rendering (FFmpeg)

The Worker connects to the Bot Server via HTTP API.
"""

import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI
from loguru import logger
import uvicorn

from worker.config import config
from worker.api.routes import router as api_router
from worker.services.model_manager import model_manager
from worker.services.text import text_service
from worker.services.image import image_service
from worker.services.video import video_service
from worker.services.voice import voice_service
from worker.services.stt import stt_service
from worker.services.music import music_service
from worker.services.editor import editor_service


# Configure logging
logger.add(
    config.LOGS_DIR / "worker_{time:YYYY-MM-DD}.log",
    rotation="1 day",
    retention="30 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
)

logger.add(
    sys.stdout,
    level="INFO",
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | {message}",
    colorize=True,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize services on startup."""
    logger.info("=" * 60)
    logger.info("⚙️ AI SHORTS STUDIO - AI Worker")
    logger.info("=" * 60)

    # Initialize model manager (detect hardware and models)
    logger.info("🔍 Initializing Model Manager...")
    await model_manager.initialize()

    # Initialize all services
    logger.info("📝 Initializing Text Service...")
    await text_service.initialize()

    logger.info("🖼 Initializing Image Service...")
    await image_service.initialize()

    logger.info("🎥 Initializing Video Service...")
    await video_service.initialize()

    logger.info("🎙 Initializing Voice Service...")
    await voice_service.initialize()

    logger.info("📝 Initializing STT Service...")
    await stt_service.initialize()

    logger.info("🎵 Initializing Music Service...")
    # Music service initializes synchronously

    logger.info("✂️ Initializing Editor Service...")
    await editor_service.initialize()

    logger.info("=" * 60)
    logger.info(f"🚀 AI Worker ready on http://{config.HOST}:{config.PORT}")
    logger.info(f"🔑 API Key: {'*' * 8}{config.API_KEY[-4:] if len(config.API_KEY) > 4 else '****'}")
    logger.info(f"💾 Low Resource Mode: {config.LOW_RESOURCE_MODE}")
    logger.info(f"🖥 GPU: {model_manager.gpu_info}")
    logger.info(f"💾 VRAM: {model_manager.vram_info}")
    logger.info("=" * 60)

    available_models = [name for name, avail in model_manager.models.items() if avail]
    unavailable_models = [name for name, avail in model_manager.models.items() if not avail]

    if available_models:
        logger.info(f"✅ Available: {', '.join(available_models)}")
    if unavailable_models:
        logger.info(f"❌ Unavailable: {', '.join(unavailable_models)}")

    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("\n👋 AI Worker shutting down...")


# Create FastAPI app
app = FastAPI(
    title="AI Shorts Studio - AI Worker API",
    description="AI Worker service for AI Shorts Studio. Handles text, image, video, voice, STT, music, and editing.",
    version="1.0.0",
    lifespan=lifespan,
)

# Register routes
app.include_router(api_router, prefix="", tags=["worker"])


@app.get("/", summary="Root endpoint")
async def root() -> dict:
    """Root endpoint - returns basic info."""
    return {
        "service": "AI Shorts Studio - AI Worker",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "jobs": "/jobs",
            "docs": "/docs",
        },
    }


def main() -> None:
    """Run the Worker server."""
    uvicorn.run(
        "worker.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
