"""
Configuration for AI Worker.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from pydantic_settings import BaseSettings


# Load .env from project root
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class WorkerConfig(BaseSettings):
    """Worker configuration."""

    # API
    HOST: str = os.getenv("WORKER_HOST", "0.0.0.0")
    PORT: int = int(os.getenv("WORKER_PORT", "8000"))
    API_KEY: str = os.getenv("WORKER_API_KEY", "default-worker-key")

    # Resource mode
    LOW_RESOURCE_MODE: bool = os.getenv("LOW_RESOURCE_MODE", "true").lower() == "true"

    # Ollama
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "qwen2:7b")

    # Image generation
    IMAGE_DEFAULT_WIDTH: int = int(os.getenv("IMAGE_DEFAULT_WIDTH", "576"))
    IMAGE_DEFAULT_HEIGHT: int = int(os.getenv("IMAGE_DEFAULT_HEIGHT", "1024"))
    IMAGE_DEFAULT_STEPS: int = int(os.getenv("IMAGE_DEFAULT_STEPS", "20"))

    # Voice
    PIPER_MODEL_PATH: str = os.getenv("PIPER_MODEL_PATH", "")
    PIPER_VOICE: str = os.getenv("PIPER_VOICE", "en_US-amy-medium")

    # Whisper
    WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "base")

    # FFmpeg
    FFMPEG_PATH: str = os.getenv("FFMPEG_PATH", "ffmpeg")

    # Paths
    TEMP_DIR: Path = BASE_DIR / os.getenv("TEMP_DIR", "temp")
    STORAGE_DIR: Path = BASE_DIR / os.getenv("STORAGE_DIR", "storage")
    LOGS_DIR: Path = BASE_DIR / os.getenv("LOGS_DIR", "logs")

    # Job limits
    MAX_CONCURRENT_JOBS: int = int(os.getenv("MAX_CONCURRENT_JOBS", "1"))
    JOB_TIMEOUT_SECONDS: int = int(os.getenv("JOB_TIMEOUT_SECONDS", "1800"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)


# Global config
config = WorkerConfig()
