import logging
from typing import Dict, Any, Optional

from worker.utils.hardware import get_hardware_info

logger = logging.getLogger(__name__)


class ModelManager:
    """
    Centralized AI model management.
    Detects available models and reports system capabilities.
    """

    def __init__(self):
        self._text_available = None
        self._image_available = None
        self._video_available = None
        self._voice_available = None
        self._stt_available = None

    # ============================================================
    # TEXT
    # ============================================================
    def _check_text(self) -> bool:
        if self._text_available is not None:
            return self._text_available
        try:
            import ollama
            models = ollama.list()
            self._text_available = bool(models and models.get("models"))
        except Exception:
            self._text_available = False
        return self._text_available

    def has_text(self) -> bool:
        return self._check_text()

    # ============================================================
    # IMAGE
    # ============================================================
    def _check_image(self) -> bool:
        if self._image_available is not None:
            return self._image_available
        try:
            from worker.services.image import ImageService
            svc = ImageService()
            self._image_available = svc.check_model()
        except Exception:
            self._image_available = False
        return self._image_available

    def has_image(self) -> bool:
        return self._check_image()

    # ============================================================
    # VIDEO
    # ============================================================
    def _check_video(self) -> bool:
        if self._video_available is not None:
            return self._video_available
        try:
            from worker.services.video import VideoService
            svc = VideoService()
            self._video_available = svc.check_model()
        except Exception:
            self._video_available = False
        return self._video_available

    def has_video(self) -> bool:
        return self._check_video()

    # ============================================================
    # VOICE / TTS
    # ============================================================
    def _check_voice(self) -> bool:
        if self._voice_available is not None:
            return self._voice_available
        try:
            from worker.services.voice import VoiceService
            svc = VoiceService()
            self._voice_available = svc.check_tts()
        except Exception:
            self._voice_available = False
        return self._voice_available

    def has_voice(self) -> bool:
        return self._check_voice()

    # ============================================================
    # STT / SUBTITLES
    # ============================================================
    def _check_stt(self) -> bool:
        if self._stt_available is not None:
            return self._stt_available
        try:
            from worker.services.stt import STTService
            svc = STTService()
            self._stt_available = svc.is_available()
        except Exception:
            self._stt_available = False
        return self._stt_available

    def has_stt(self) -> bool:
        return self._check_stt()

    # ============================================================
    # CAPABILITIES
    # ============================================================
    def get_capabilities(self) -> Dict[str, bool]:
        """Get all system capabilities."""
        from worker.utils.ffmpeg import check_ffmpeg_available

        return {
            "TEXT": self.has_text(),
            "IMAGE": self.has_image(),
            "VIDEO": self.has_video(),
            "VOICE": self.has_voice(),
            "STT": self.has_stt(),
            "MUSIC": True,
            "SFX": True,
            "EDITING": check_ffmpeg_available()
        }

    # ============================================================
    # MODEL STATUSES
    # ============================================================
    def get_model_statuses(self) -> Dict[str, list]:
        """Get detailed status of all model categories."""
        statuses = {
            "text": [],
            "image": [],
            "video": [],
            "voice": [],
            "stt": [],
            "editing": []
        }

        # Text
        try:
            import ollama
            models = ollama.list()
            for m in models.get("models", []):
                statuses["text"].append({
                    "name": m.get("name", "unknown"),
                    "available": True,
                    "backend": "Ollama"
                })
        except Exception:
            statuses["text"].append({
                "name": "Ollama",
                "available": False,
                "backend": "Ollama",
                "note": "Install: pip install ollama && ollama pull qwen2:7b"
            })

        # Image
        try:
            from worker.services.image import ImageService
            svc = ImageService()
            info = svc.get_model_info()
            statuses["image"].append({
                "name": info["name"],
                "available": info["available"],
                "backend": "diffusers",
                "device": info.get("device", "cpu"),
                "vram_gb": info.get("vram_gb", 0),
                "requirements": "NVIDIA GPU 4GB+ VRAM, PyTorch, diffusers"
            })
        except Exception as e:
            statuses["image"].append({"name": "Stable Diffusion", "available": False, "error": str(e)[:100]})

        # Video
        try:
            from worker.services.video import VideoService
            svc = VideoService()
            for m in svc.get_available_models_info():
                statuses["video"].append({
                    **m,
                    "backend": "diffusers",
                    "requirements": "NVIDIA GPU 10GB+ VRAM"
                })
        except Exception as e:
            statuses["video"].append({"name": "Video models", "available": False, "error": str(e)[:100]})

        # Voice / TTS
        try:
            from worker.services.voice import VoiceService
            svc = VoiceService()
            for m in svc.get_available_models_info():
                statuses["voice"].append({
                    **m,
                    "options": "kokoro, piper-tts, gTTS"
                })
        except Exception as e:
            statuses["voice"].append({"name": "TTS engines", "available": False, "error": str(e)[:100]})

        # STT
        try:
            from worker.services.stt import STTService
            svc = STTService()
            statuses["stt"].append({
                "name": "Whisper",
                "available": svc.is_available(),
                "backend": "openai-whisper",
                "requirements": "pip install openai-whisper, ffmpeg"
            })
        except Exception as e:
            statuses["stt"].append({"name": "Whisper", "available": False, "error": str(e)[:100]})

        # Editing
        from worker.utils.ffmpeg import check_ffmpeg_available
        statuses["editing"].append({
            "name": "FFmpeg",
            "available": check_ffmpeg_available(),
            "backend": "System",
            "requirements": "Install FFmpeg on system"
        })

        return statuses


# Global instance
model_manager = ModelManager()
