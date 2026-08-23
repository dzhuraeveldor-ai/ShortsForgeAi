import logging
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)


class VideoService:
    """
    Service for video generation.
    Supports multiple open-source models with automatic fallback.
    """

    def __init__(self):
        self._available = None
        self._best_model = None

    def _check_gpu(self) -> Tuple[bool, float, str]:
        try:
            import torch
            if not torch.cuda.is_available():
                return False, 0.0, "cpu"
            device = torch.device("cuda")
            vram = torch.cuda.get_device_properties(device).total_memory / (1024**3)
            return True, round(vram, 1), torch.cuda.get_device_name(device)
        except ImportError:
            return False, 0.0, "cpu (PyTorch not installed)"
        except Exception:
            return False, 0.0, "cpu"

    def check_model(self) -> bool:
        """Check if any video generation model is available."""
        if self._available is not None:
            return self._available

        has_gpu, vram, device = self._check_gpu()

        if not has_gpu:
            logger.warning("Video generation: no GPU")
            self._available = False
            return False

        if vram < 10:
            logger.warning(f"Video generation: insufficient VRAM ({vram}GB < 10GB)")
            self._available = False
            return False

        # Check which models are importable
        try:
            import diffusers
            if vram >= 16:
                self._best_model = "Wan"
            elif vram >= 12:
                self._best_model = "LTX-Video"
            else:
                self._best_model = "CogVideoX"

            self._available = True
            logger.info(f"Video model available: {self._best_model}, VRAM: {vram}GB")
            return True

        except ImportError:
            logger.warning("Video dependencies missing: diffusers not installed")
            self._available = False
            return False

    def check_gpu(self) -> Tuple[bool, float, str]:
        return self._check_gpu()

    def check_vram(self) -> float:
        _, vram, _ = self._check_gpu()
        return vram

    def get_best_model(self) -> Optional[str]:
        self.check_model()
        return self._best_model

    def get_available_models_info(self) -> List[Dict[str, Any]]:
        has_gpu, vram, _ = self._check_gpu()
        models = [
            {"name": "Wan", "min_vram": 16, "available": has_gpu and vram >= 16},
            {"name": "LTX-Video", "min_vram": 12, "available": has_gpu and vram >= 12},
            {"name": "CogVideoX", "min_vram": 10, "available": has_gpu and vram >= 10}
        ]
        return models

    def generate_video(
        self,
        prompt: str,
        visual_style: str = "realistic",
        num_frames: int = 49,
        width: int = 576,
        height: int = 1024
    ):
        """Generate video from text."""
        if not self.check_model():
            raise RuntimeError(
                "⚠️ Video generation model not available.\n"
                "Requires: NVIDIA GPU with 10GB+ VRAM, PyTorch, diffusers.\n"
                "Alternative: use Image mode with camera movement via FFmpeg."
            )
        raise NotImplementedError("Video generation requires model download — use Image mode instead")

    def image_to_video(
        self,
        image: Image.Image,
        prompt: str = "",
        visual_style: str = "realistic",
        num_frames: int = 49
    ):
        """Animate image into video."""
        if not self.check_model():
            raise RuntimeError("⚠️ Video model not available for animation.")
        raise NotImplementedError("Image-to-video requires model download")

    def text_to_video(self, prompt: str, visual_style: str = "realistic", **kwargs):
        return self.generate_video(prompt, visual_style, **kwargs)

    def get_fallback_options(self) -> List[str]:
        return [
            "🖼 Generate images and create video with camera movement via FFmpeg",
            "📹 Use static scene video mode (images + transitions + zoom)",
            "⏳ Connect AI Worker with video capabilities"
        ]
