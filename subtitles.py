import logging
import os
from typing import Optional, Dict, Any

from worker.services.stt import STTService

logger = logging.getLogger(__name__)


class SubtitleService:
    """
    Service for subtitle generation with automatic style selection by niche.
    """

    # Style presets for different niches
    STYLE_PRESETS = {
        "horror": {
            "name": "Cinematic Horror",
            "font": "Arial",
            "font_size": 28,
            "color": "#FFFFFF",
            "outline_color": "#000000",
            "outline_width": 3,
            "shadow": True,
            "position": "bottom",
            "animation": "fade"
        },
        "facts": {
            "name": "Bold Highlight",
            "font": "Impact",
            "font_size": 32,
            "color": "#FFFF00",
            "outline_color": "#000000",
            "outline_width": 4,
            "shadow": True,
            "position": "center",
            "animation": "pop"
        },
        "motivation": {
            "name": "Energetic",
            "font": "Impact",
            "font_size": 36,
            "color": "#FF4500",
            "outline_color": "#000000",
            "outline_width": 4,
            "shadow": True,
            "position": "center",
            "animation": "zoom"
        },
        "funny": {
            "name": "Dynamic",
            "font": "Comic Sans MS",
            "font_size": 30,
            "color": "#FFFFFF",
            "outline_color": "#FF69B4",
            "outline_width": 3,
            "shadow": True,
            "position": "varying",
            "animation": "bounce"
        },
        "luxury": {
            "name": "Elegant",
            "font": "Georgia",
            "font_size": 26,
            "color": "#FFD700",
            "outline_color": "#000000",
            "outline_width": 2,
            "shadow": True,
            "position": "bottom",
            "animation": "fade"
        },
        "news": {
            "name": "Clean Modern",
            "font": "Roboto",
            "font_size": 26,
            "color": "#FFFFFF",
            "outline_color": "#000000",
            "outline_width": 2,
            "shadow": False,
            "position": "bottom",
            "animation": "none"
        },
        "default": {
            "name": "Clean Readable",
            "font": "Arial",
            "font_size": 28,
            "color": "#FFFFFF",
            "outline_color": "#000000",
            "outline_width": 3,
            "shadow": True,
            "position": "bottom",
            "animation": "fade"
        }
    }

    def __init__(self, stt_service: Optional[STTService] = None):
        self.stt = stt_service or STTService()

    def is_available(self) -> bool:
        return self.stt.is_available()

    def get_subtitle_style(self, niche: str = "") -> Dict[str, Any]:
        """Auto-select subtitle style based on niche."""
        niche_lower = niche.lower() if niche else ""

        for keyword, style in self.STYLE_PRESETS.items():
            if keyword in niche_lower:
                return style

        if any(k in niche_lower for k in ["documentary", "history", "education"]):
            return self.STYLE_PRESETS["news"]
        if any(k in niche_lower for k in ["fitness", "sports"]):
            return self.STYLE_PRESETS["motivation"]
        if any(k in niche_lower for k in ["business", "money"]):
            return self.STYLE_PRESETS["luxury"]
        if any(k in niche_lower for k in ["comedy", "viral"]):
            return self.STYLE_PRESETS["funny"]
        if any(k in niche_lower for k in ["science", "space", "technology"]):
            return self.STYLE_PRESETS["facts"]

        return self.STYLE_PRESETS["default"]

    def generate_subtitles(
        self,
        audio_path: str,
        output_dir: str,
        language: str = "en",
        niche: str = "",
        base_filename: str = "subtitles"
    ) -> Dict[str, Any]:
        """Generate subtitles with auto-selected style."""
        if not self.is_available():
            raise RuntimeError(
                "⚠️ Subtitle generation requires Whisper STT.\n"
                "Install: pip install openai-whisper"
            )

        os.makedirs(output_dir, exist_ok=True)

        srt_path = os.path.join(output_dir, f"{base_filename}.srt")
        vtt_path = os.path.join(output_dir, f"{base_filename}.vtt")

        self.stt.generate_srt(audio_path, srt_path, language)
        self.stt.generate_vtt(audio_path, vtt_path, language)

        word_timestamps = self.stt.get_word_timestamps(audio_path, language)
        style = self.get_subtitle_style(niche)

        result = {
            "srt_path": srt_path,
            "vtt_path": vtt_path,
            "style": style,
            "word_timestamps": word_timestamps,
            "language": language,
            "niche": niche
        }

        logger.info(
            f"Subtitles generated: {srt_path} | "
            f"Style: {style['name']} | "
            f"Words: {len(word_timestamps)}"
        )

        return result
