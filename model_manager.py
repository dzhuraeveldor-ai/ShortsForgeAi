"""
Model Manager - detects available AI models and manages them.
"""

import asyncio
from typing import Optional
from loguru import logger


class ModelManager:
    """Detects and manages available AI models."""

    def __init__(self):
        self._models: dict[str, bool] = {}
        self._gpu_info: Optional[str] = None
        self._vram_info: Optional[str] = None
        self._initialized = False

    async def initialize(self) -> None:
        """Detect all available models and hardware."""
        logger.info("🔍 Model Manager: detecting available models...")

        # Detect GPU
        await self._detect_gpu()

        # Detect each model type
        self._models["text"] = await self._detect_text_model()
        self._models["image"] = await self._detect_image_model()
        self._models["video"] = await self._detect_video_model()
        self._models["voice"] = await self._detect_voice_model()
        self._models["stt"] = await self._detect_stt_model()
        self._models["editing"] = await self._detect_editing()

        self._initialized = True

        logger.info(f"📊 Model detection complete:")
        for name, available in self._models.items():
            status = "✅" if available else "❌"
            logger.info(f"   {status} {name}")

    async def _detect_gpu(self) -> None:
        """Detect GPU availability."""
        try:
            # Try torch first
            import subprocess
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0 and result.stdout.strip():
                lines = result.stdout.strip().split("\n")
                if lines:
                    parts = lines[0].split(", ")
                    if len(parts) >= 2:
                        self._gpu_info = parts[0].strip()
                        vram_mb = float(parts[1].strip())
                        if vram_mb >= 1024:
                            self._vram_info = f"{vram_mb / 1024:.1f} GB"
                        else:
                            self._vram_info = f"{vram_mb:.0f} MB"
                        logger.info(f"🖥 GPU detected: {self._gpu_info} ({self._vram_info})")
                        return

            # Try torch CUDA check
            try:
                import torch
                if torch.cuda.is_available():
                    device = torch.cuda.get_device_name(0)
                    vram = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
                    self._gpu_info = device
                    self._vram_info = f"{vram:.1f} GB"
                    logger.info(f"🖥 GPU detected via torch: {self._gpu_info} ({self._vram_info})")
                    return
            except ImportError:
                pass

            self._gpu_info = "CPU only"
            self._vram_info = "N/A"
            logger.info("🖥 No GPU detected, using CPU")

        except Exception as e:
            logger.warning(f"GPU detection failed: {e}")
            self._gpu_info = "Unknown"
            self._vram_info = "Unknown"

    async def _detect_text_model(self) -> bool:
        """Detect Ollama availability."""
        try:
            import httpx
            from worker.config import config

            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{config.OLLAMA_BASE_URL}/api/tags")
                if response.status_code == 200:
                    data = response.json()
                    models = data.get("models", [])
                    if models:
                        logger.info(f"📝 Ollama detected with {len(models)} models")
                        for m in models:
                            logger.info(f"   • {m.get('name', 'unknown')}")
                        return True
                    else:
                        logger.warning("📝 Ollama running but no models installed")
                        return False
                return False
        except Exception as e:
            logger.warning(f"📝 Ollama not available: {e}")
            return False

    async def _detect_image_model(self) -> bool:
        """Detect image generation models."""
        try:
            import diffusers  # noqa: F401
            import torch  # noqa: F401
            logger.info("🖼 Diffusers library available for image generation")
            return True
        except ImportError:
            logger.warning("🖼 Diffusers not installed - image generation unavailable")
            return False

    async def _detect_video_model(self) -> bool:
        """Detect video generation models."""
        # Video models are heavy and optional
        try:
            # Check for any video generation libraries
            import torch  # noqa: F401
            # We don't auto-detect specific video models as they require manual setup
            logger.info("🎥 Video model interface available (requires manual model download)")
            return False  # Return False until user explicitly sets up a video model
        except ImportError:
            logger.warning("🎥 Video generation unavailable - torch not found")
            return False

    async def _detect_voice_model(self) -> bool:
        """Detect TTS models."""
        # Check Piper TTS
        try:
            import piper  # noqa: F401
            logger.info("🎙 Piper TTS available")
            return True
        except ImportError:
            pass

        # Check kokoro
        try:
            import kokoro  # noqa: F401
            logger.info("🎙 Kokoro TTS available")
            return True
        except ImportError:
            pass

        logger.warning("🎙 No TTS engine available (install piper-tts or kokoro)")
        return False

    async def _detect_stt_model(self) -> bool:
        """Detect Whisper for STT/subtitles."""
        try:
            import whisper  # noqa: F401
            logger.info("📝 Whisper available for subtitles/STT")
            return True
        except ImportError:
            logger.warning("📝 Whisper not installed - subtitles unavailable")
            return False

    async def _detect_editing(self) -> bool:
        """Detect FFmpeg for video editing."""
        try:
            import subprocess
            from worker.config import config
            result = subprocess.run(
                [config.FFMPEG_PATH, "-version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                version_line = result.stdout.split("\n")[0]
                logger.info(f"✂️ FFmpeg available: {version_line[:80]}")
                return True
        except Exception as e:
            logger.warning(f"✂️ FFmpeg not available: {e}")
        return False

    @property
    def models(self) -> dict[str, bool]:
        """Get available models status."""
        return self._models.copy()

    @property
    def gpu_info(self) -> Optional[str]:
        """Get GPU info."""
        return self._gpu_info

    @property
    def vram_info(self) -> Optional[str]:
        """Get VRAM info."""
        return self._vram_info

    def is_available(self, model_type: str) -> bool:
        """Check if a specific model type is available."""
        return self._models.get(model_type, False)


# Global model manager
model_manager = ModelManager()
