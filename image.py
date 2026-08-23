import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from PIL import Image

from worker.services.style_manager import StyleManager

logger = logging.getLogger(__name__)


class ImageService:
    """
    Service for generating images for Shorts scenes.
    Supports Stable Diffusion models with fallback logic.
    """

    def __init__(self):
        self._pipeline = None
        self._available = None
        self._model_name = "SD"
        self._device = "cpu"
        self._vram_gb = 0

    def _check_gpu(self) -> Tuple[bool, float, str]:
        """Check GPU availability and VRAM."""
        try:
            import torch
            if not torch.cuda.is_available():
                return False, 0.0, "cpu"
            device = torch.device("cuda")
            vram = torch.cuda.get_device_properties(device).total_memory / (1024**3)
            gpu_name = torch.cuda.get_device_name(device)
            return True, round(vram, 1), gpu_name
        except ImportError:
            return False, 0.0, "cpu (PyTorch not installed)"
        except Exception as e:
            logger.warning(f"GPU check failed: {e}")
            return False, 0.0, "cpu"

    def check_model(self) -> bool:
        """Check if image generation model is available."""
        if self._available is not None:
            return self._available

        try:
            import torch
            from diffusers import StableDiffusionPipeline

            has_gpu, vram, device = self._check_gpu()
            self._device = "cuda" if has_gpu else "cpu"
            self._vram_gb = vram

            if not has_gpu:
                logger.warning("Image generation: no GPU detected")
                self._available = False
                return False

            if vram < 4:
                logger.warning(f"Image generation: insufficient VRAM ({vram}GB < 4GB)")
                self._available = False
                return False

            self._model_name = "SD 1.5" if vram < 8 else "SDXL"
            self._available = True
            logger.info(f"Image model available: {self._model_name}, VRAM: {vram}GB")
            return True

        except ImportError as e:
            logger.warning(f"Image dependencies missing: {e}")
            self._available = False
            return False
        except Exception as e:
            logger.warning(f"Image model check failed: {e}")
            self._available = False
            return False

    def check_gpu(self) -> Tuple[bool, float, str]:
        """Public GPU check method."""
        return self._check_gpu()

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information."""
        has_gpu, vram, device = self._check_gpu()
        return {
            "name": self._model_name,
            "available": self.check_model(),
            "device": device,
            "vram_gb": vram,
            "has_gpu": has_gpu
        }

    def _load_pipeline(self):
        """Load the appropriate image generation pipeline."""
        if self._pipeline is not None:
            return self._pipeline

        import torch
        from diffusers import StableDiffusionPipeline

        model_id = "runwayml/stable-diffusion-v1-5" if self._vram_gb < 8 else "stabilityai/stable-diffusion-xl-base-1.0"

        self._pipeline = StableDiffusionPipeline.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            use_safetensors=True
        )
        self._pipeline = self._pipeline.to("cuda")
        self._pipeline.enable_attention_slicing()

        logger.info(f"Image pipeline loaded: {model_id}")
        return self._pipeline

    def build_prompt(
        self,
        visual_description: str,
        visual_style: str = "realistic",
        character_ref: Optional[Dict[str, str]] = None,
        aspect_ratio: str = "9:16"
    ) -> str:
        """Build complete positive image prompt with style."""
        base = visual_description
        if character_ref and character_ref.get("Full Description"):
            base = f"{character_ref['Full Description']}, {base}"
        return StyleManager.build_prompt(base, visual_style, aspect_ratio)

    def build_negative_prompt(self, visual_style: str = "realistic") -> str:
        """Build negative prompt."""
        return StyleManager.build_negative_prompt(visual_style)

    def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        visual_style: str = "realistic",
        width: int = 512,
        height: int = 896,
        num_inference_steps: int = 25,
        guidance_scale: float = 7.5
    ) -> Image.Image:
        """Generate a single image."""
        if not self.check_model():
            raise RuntimeError(
                "⚠️ Image generation model not available. "
                "Requires NVIDIA GPU with 4GB+ VRAM, PyTorch, and diffusers."
            )

        try:
            import torch
            pipeline = self._load_pipeline()

            with torch.no_grad():
                result = pipeline(
                    prompt=prompt,
                    negative_prompt=negative_prompt or None,
                    width=width,
                    height=height,
                    num_inference_steps=num_inference_steps,
                    guidance_scale=guidance_scale
                )

            return result.images[0]

        except Exception as e:
            logger.error(f"Image generation failed: {e}")
            raise RuntimeError(f"Image generation failed: {str(e)}")

    def generate_scene_images(
        self,
        scenes: List[Dict[str, Any]],
        visual_style: str = "realistic",
        character_ref: Optional[Dict[str, str]] = None,
        output_dir: str = "./temp"
    ) -> List[Dict[str, Any]]:
        """Generate images for all scenes."""
        if not self.check_model():
            raise RuntimeError("⚠️ Image generation model not available.")

        os.makedirs(output_dir, exist_ok=True)
        results = []

        for i, scene in enumerate(scenes):
            scene_num = scene.get("Scene Number", i + 1)
            visual_desc = scene.get("Visual Description", "")

            positive = self.build_prompt(visual_desc, visual_style, character_ref)
            negative = self.build_negative_prompt(visual_style)

            try:
                image = self.generate_image(
                    prompt=positive,
                    negative_prompt=negative,
                    visual_style=visual_style
                )

                image_path = os.path.join(output_dir, f"scene_{scene_num:02d}.png")
                image.save(image_path, "PNG", quality=95)

                scene_result = dict(scene)
                scene_result["image_path"] = image_path
                scene_result["image_prompt_used"] = positive
                results.append(scene_result)

                logger.info(f"Scene {scene_num} image generated: {image_path}")

            except Exception as e:
                logger.error(f"Scene {scene_num} image failed: {e}")
                scene_result = dict(scene)
                scene_result["error"] = str(e)
                scene_result["image_path"] = os.path.join(output_dir, f"scene_{scene_num:02d}.png")
                results.append(scene_result)

        return results
