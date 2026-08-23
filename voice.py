import logging
import os
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger(__name__)


class VoiceService:
    """
    Service for voice generation (TTS).
    Supports Kokoro and Piper with automatic fallback.
    """

    def __init__(self):
        self._available = None
        self._model_name = None

    def check_tts(self) -> bool:
        """Check if any TTS engine is available."""
        if self._available is not None:
            return self._available

        # Try Kokoro first
        try:
            import kokoro
            self._model_name = "Kokoro"
            self._available = True
            logger.info("TTS available: Kokoro")
            return True
        except ImportError:
            pass

        # Try Piper
        try:
            import piper
            self._model_name = "Piper"
            self._available = True
            logger.info("TTS available: Piper")
            return True
        except ImportError:
            pass

        # Try gTTS as last resort (online)
        try:
            import gtts
            self._model_name = "gTTS"
            self._available = True
            logger.info("TTS available: gTTS (online)")
            return True
        except ImportError:
            pass

        logger.warning("No TTS engine available. Install: kokoro, piper-tts, or gTTS")
        self._available = False
        return False

    def select_voice(
        self,
        niche: str = "",
        content_type: str = "",
        script: str = "",
        user_preference: str = "automatic"
    ) -> str:
        """Auto-select voice based on content."""
        if user_preference != "automatic":
            return user_preference

        niche_lower = niche.lower()

        male_niches = ["horror", "true crime", "business", "money", "fitness",
                       "sports", "cars", "technology", "programming", "science",
                       "space", "mystery"]
        female_niches = ["relationships", "psychology", "animals", "luxury",
                         "beauty", "fashion", "food", "travel", "education",
                         "storytelling"]

        for kw in male_niches:
            if kw in niche_lower:
                return "male"
        for kw in female_niches:
            if kw in niche_lower:
                return "female"

        return "female"

    def calculate_speed(
        self,
        word_count: int,
        target_duration_seconds: int,
        content_type: str = "",
        user_preference: str = "automatic"
    ) -> float:
        """Calculate optimal speech speed to fit target duration."""
        if user_preference != "automatic":
            try:
                return float(user_preference)
            except (ValueError, TypeError):
                pass

        base_wpm = 150
        if target_duration_seconds <= 0:
            return 1.0

        target_wpm = (word_count / target_duration_seconds) * 60
        speed = target_wpm / base_wpm
        speed = max(0.8, min(1.2, speed))

        ct = content_type.lower()
        if any(k in ct for k in ["horror", "dramatic", "mystery"]):
            speed = max(0.8, speed * 0.95)
        elif any(k in ct for k in ["energetic", "viral", "funny"]):
            speed = min(1.2, speed * 1.05)

        return round(speed, 2)

    def generate_voice(
        self,
        text: str,
        output_path: str,
        voice: str = "automatic",
        voice_style: str = "automatic",
        speed: float = 1.0,
        language: str = "en_US",
        niche: str = "",
        content_type: str = "",
        target_duration: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate voice audio and save to file."""
        if not self.check_tts():
            raise RuntimeError(
                "⚠️ No TTS engine available.\n"
                "Install one of: pip install kokoro, pip install piper-tts, or pip install gTTS"
            )

        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

        word_count = len(text.split())

        # Auto-select voice
        selected_voice = self.select_voice(niche, content_type, text, voice)

        # Auto-calculate speed if target duration provided
        if target_duration and speed == 1.0:
            speed = self.calculate_speed(word_count, target_duration, content_type)

        try:
            if self._model_name == "Kokoro":
                import kokoro
                model = kokoro.Kokoro()
                audio = model.generate(text=text, voice=selected_voice, speed=speed)
                sr = model.sample_rate
                import soundfile as sf
                sf.write(output_path, audio, sr)

            elif self._model_name == "Piper":
                import piper
                voice_file = "en_US-amy-medium" if selected_voice == "female" else "en_US-ryan-medium"
                model = piper.PiperVoice.load(voice_file)
                audio = model.synthesize(text, speed=speed)
                sr = model.sample_rate
                import soundfile as sf
                sf.write(output_path, audio, sr)

            elif self._model_name == "gTTS":
                from gtts import gTTS
                lang = "en"
                tld = "us" if "US" in language.upper() else "co.uk"
                tts = gTTS(text=text, lang=lang, tld=tld, slow=speed < 0.9)
                # Save as mp3 first, then convert to wav
                mp3_path = output_path + ".tmp.mp3"
                tts.save(mp3_path)
                # Convert using ffmpeg
                from worker.utils.ffmpeg import run_ffmpeg
                run_ffmpeg(["-i", mp3_path, "-ar", "22050", "-ac", "1", output_path], "gTTS convert")
                os.remove(mp3_path)
                sr = 22050

            # Get actual duration
            import soundfile as sf
            audio_data, sr = sf.read(output_path)
            duration = len(audio_data) / sr

            result = {
                "path": output_path,
                "sample_rate": sr,
                "duration_seconds": round(duration, 2),
                "word_count": word_count,
                "voice_used": selected_voice,
                "style_used": voice_style,
                "speed_used": speed,
                "model_used": self._model_name,
                "language": language
            }

            logger.info(
                f"Voice generated: {duration:.1f}s, {word_count} words, "
                f"{self._model_name}, voice={selected_voice}, speed={speed}x"
            )
            return result

        except Exception as e:
            logger.error(f"Voice generation failed: {e}")
            raise RuntimeError(f"Voice generation failed: {str(e)}")

    def get_available_models_info(self) -> list:
        return [{"name": self._model_name or "none", "available": self.check_tts()}]
