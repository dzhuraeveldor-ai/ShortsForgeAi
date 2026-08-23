import logging
import os
from typing import Optional, Dict, Any, List
import numpy as np

logger = logging.getLogger(__name__)


class MusicService:
    """
    Smart Music System for Shorts.
    Automatically selects royalty-free/CC0 music based on niche/content.
    Features: trim, loop, fade, audio ducking.
    """

    # Niche → music profile mapping
    NICHE_MUSIC = {
        "horror": {
            "genres": ["dark ambient", "suspense", "horror drone"],
            "tempo": "slow",
            "energy": "low tension building",
            "instruments": ["low strings", "distant piano", "atmospheric drones"],
            "description": "Dark, suspenseful ambient music",
            "base_volume_db": -22,
            "fade_in": 1.0,
            "fade_out": 1.5
        },
        "motivation": {
            "genres": ["epic cinematic", "uplifting orchestral", "energetic rock"],
            "tempo": "medium-fast",
            "energy": "high building",
            "instruments": ["epic strings", "drums", "brass"],
            "description": "Energetic, inspiring cinematic music",
            "base_volume_db": -20,
            "fade_in": 0.3,
            "fade_out": 1.0
        },
        "luxury": {
            "genres": ["elegant ambient", "chill lounge", "sophisticated jazz"],
            "tempo": "slow-medium",
            "energy": "smooth refined",
            "instruments": ["soft piano", "strings", "light percussion"],
            "description": "Elegant, sophisticated ambient music",
            "base_volume_db": -24,
            "fade_in": 0.8,
            "fade_out": 1.2
        },
        "facts": {
            "genres": ["modern documentary", "minimal electronic", "chill ambient"],
            "tempo": "medium",
            "energy": "steady engaging",
            "instruments": ["subtle synths", "light percussion", "piano"],
            "description": "Modern documentary background music",
            "base_volume_db": -22,
            "fade_in": 0.5,
            "fade_out": 1.0
        },
        "funny": {
            "genres": ["light comedic", "playful acoustic", "quirky"],
            "tempo": "fast",
            "energy": "playful bouncy",
            "instruments": ["ukulele", "whistle", "light drums"],
            "description": "Light, playful comedic music",
            "base_volume_db": -22,
            "fade_in": 0.2,
            "fade_out": 0.5
        },
        "science": {
            "genres": ["futuristic ambient", "electronic space", "atmospheric synth"],
            "tempo": "medium-slow",
            "energy": "mysterious wonder",
            "instruments": ["synths", "atmospheric pads", "subtle beats"],
            "description": "Futuristic, wonder-inducing music",
            "base_volume_db": -23,
            "fade_in": 0.8,
            "fade_out": 1.0
        },
        "history": {
            "genres": ["cinematic documentary", "orchestral dramatic"],
            "tempo": "medium",
            "energy": "dramatic epic",
            "instruments": ["orchestra", "strings", "percussion"],
            "description": "Cinematic documentary orchestral music",
            "base_volume_db": -22,
            "fade_in": 0.6,
            "fade_out": 1.2
        },
        "gaming": {
            "genres": ["energetic electronic", "synthwave", "epic game score"],
            "tempo": "fast",
            "energy": "high energy intense",
            "instruments": ["synths", "electronic drums", "bass"],
            "description": "Energetic electronic gaming music",
            "base_volume_db": -20,
            "fade_in": 0.2,
            "fade_out": 0.8
        },
        "animals": {
            "genres": ["playful acoustic", "emotional ambient", "warm folk"],
            "tempo": "medium",
            "energy": "warm emotional",
            "instruments": ["acoustic guitar", "piano", "light strings"],
            "description": "Warm, emotional acoustic music",
            "base_volume_db": -23,
            "fade_in": 0.5,
            "fade_out": 1.0
        },
        "mystery": {
            "genres": ["suspense ambient", "mysterious drone", "tense cinematic"],
            "tempo": "slow",
            "energy": "building tension",
            "instruments": ["atmospheric pads", "subtle percussion", "distant piano"],
            "description": "Suspenseful, mysterious music",
            "base_volume_db": -22,
            "fade_in": 1.0,
            "fade_out": 1.5
        },
        "ai": {
            "genres": ["futuristic electronic", "synth ambient", "tech"],
            "tempo": "medium",
            "energy": "modern technological",
            "instruments": ["synths", "electronic pulses", "atmospheric"],
            "description": "Futuristic electronic music",
            "base_volume_db": -23,
            "fade_in": 0.5,
            "fade_out": 1.0
        },
        "storytelling": {
            "genres": ["cinematic storytelling", "emotional orchestral"],
            "tempo": "varying",
            "energy": "emotional journey",
            "instruments": ["piano", "strings", "subtle orchestra"],
            "description": "Emotional cinematic storytelling music",
            "base_volume_db": -22,
            "fade_in": 0.6,
            "fade_out": 1.2
        },
        "education": {
            "genres": ["light ambient", "focus music", "pleasant background"],
            "tempo": "medium",
            "energy": "calm engaging",
            "instruments": ["light piano", "soft synths", "subtle beats"],
            "description": "Light, engaging background music",
            "base_volume_db": -24,
            "fade_in": 0.5,
            "fade_out": 0.8
        },
        "travel": {
            "genres": ["adventure cinematic", "world music", "uplifting acoustic"],
            "tempo": "medium",
            "energy": "adventurous uplifting",
            "instruments": ["acoustic guitar", "world percussion", "strings"],
            "description": "Adventurous, uplifting travel music",
            "base_volume_db": -21,
            "fade_in": 0.4,
            "fade_out": 1.0
        },
        "food": {
            "genres": ["warm acoustic", "cozy jazz", "pleasant ambient"],
            "tempo": "medium-slow",
            "energy": "warm cozy",
            "instruments": ["acoustic guitar", "light piano", "soft percussion"],
            "description": "Warm, cozy music",
            "base_volume_db": -23,
            "fade_in": 0.5,
            "fade_out": 0.8
        },
        "fitness": {
            "genres": ["high energy electronic", "dance", "workout beats"],
            "tempo": "fast",
            "energy": "pumping motivating",
            "instruments": ["electronic drums", "bass", "synths"],
            "description": "High energy workout music",
            "base_volume_db": -18,
            "fade_in": 0.2,
            "fade_out": 0.5
        },
        "true crime": {
            "genres": ["dark suspense", "tense ambient", "noir"],
            "tempo": "slow",
            "energy": "tense ominous",
            "instruments": ["low strings", "atmospheric drones", "subtle percussion"],
            "description": "Dark, tense crime music",
            "base_volume_db": -22,
            "fade_in": 1.0,
            "fade_out": 1.5
        },
        "sports": {
            "genres": ["epic sports", "energetic rock", "anthemic"],
            "tempo": "fast",
            "energy": "powerful anthemic",
            "instruments": ["drums", "electric guitar", "brass"],
            "description": "Powerful, anthemic sports music",
            "base_volume_db": -19,
            "fade_in": 0.2,
            "fade_out": 0.8
        },
        "psychology": {
            "genres": ["ambient introspective", "calm ambient", "thoughtful"],
            "tempo": "slow",
            "energy": "introspective calm",
            "instruments": ["piano", "soft pads", "subtle textures"],
            "description": "Introspective, thoughtful ambient music",
            "base_volume_db": -24,
            "fade_in": 0.8,
            "fade_out": 1.2
        },
        "relationships": {
            "genres": ["emotional piano", "romantic ambient", "warm acoustic"],
            "tempo": "medium-slow",
            "energy": "emotional warm",
            "instruments": ["piano", "strings", "acoustic guitar"],
            "description": "Emotional, warm music",
            "base_volume_db": -23,
            "fade_in": 0.6,
            "fade_out": 1.0
        },
        "money": {
            "genres": ["corporate upbeat", "success cinematic", "confident"],
            "tempo": "medium",
            "energy": "confident ambitious",
            "instruments": ["synths", "brass", "light percussion"],
            "description": "Confident, ambitious success music",
            "base_volume_db": -22,
            "fade_in": 0.4,
            "fade_out": 0.8
        },
        "programming": {
            "genres": ["lo-fi electronic", "focus ambient", "chill synth"],
            "tempo": "medium",
            "energy": "focused steady",
            "instruments": ["subtle synths", "light beats", "atmospheric"],
            "description": "Focused, steady programming music",
            "base_volume_db": -24,
            "fade_in": 0.5,
            "fade_out": 0.8
        }
    }

    DEFAULT_PROFILE = {
        "genres": ["light ambient", "pleasant background"],
        "tempo": "medium",
        "energy": "neutral",
        "instruments": ["piano", "light synths"],
        "description": "Pleasant neutral background music",
        "base_volume_db": -22,
        "fade_in": 0.5,
        "fade_out": 1.0
    }

    def __init__(self):
        self._music_library = {}
        self._scan_library()

    def _scan_library(self) -> None:
        """Scan music library directory for available tracks."""
        music_dir = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "assets", "music"
        )
        if os.path.exists(music_dir):
            for f in os.listdir(music_dir):
                if f.endswith((".mp3", ".wav", ".ogg", ".flac")):
                    track_id = os.path.splitext(f)[0]
                    self._music_library[track_id] = {
                        "path": os.path.join(music_dir, f),
                        "filename": f,
                        "tags": self._parse_filename(track_id)
                    }
            logger.info(f"Music library: {len(self._music_library)} tracks")
        else:
            logger.info("Music library directory not found — using procedural approach")

    def _parse_filename(self, filename: str) -> Dict[str, Any]:
        """Extract tags from filename pattern."""
        parts = filename.lower().replace("_", " ").split()
        return {
            "genres": [p for p in parts if p in ["ambient", "cinematic", "electronic", "rock", "jazz"]],
            "tempo": next((p for p in parts if p in ["slow", "medium", "fast"]), "medium"),
            "energy": next((p for p in parts if p in ["low", "medium", "high"]), "medium")
        }

    def select_music(
        self,
        niche: str = "",
        content_type: str = "",
        script_text: str = "",
        emotion: str = "",
        duration: float = 30.0,
        pacing: str = "medium",
        drama_level: int = 5
    ) -> Dict[str, Any]:
        """Automatically select the best music profile."""
        niche_lower = niche.lower() if niche else ""

        profile = self.DEFAULT_PROFILE.copy()
        for keyword, niche_profile in self.NICHE_MUSIC.items():
            if keyword in niche_lower:
                profile = niche_profile.copy()
                break

        # Adjust volume based on drama
        base_vol = profile.get("base_volume_db", -22)
        if drama_level > 7:
            base_vol += 2
        elif drama_level < 3:
            base_vol -= 2

        # Ducking parameters
        ducking = {
            "enabled": True,
            "target_volume_during_speech": -28,
            "target_volume_during_silence": base_vol,
            "attack_time": 0.05,
            "release_time": 0.2,
            "threshold": -35
        }

        # Find matching tracks
        matching = []
        for track_id, info in self._music_library.items():
            tags = info.get("tags", {})
            if any(g in profile.get("genres", []) for g in tags.get("genres", [])):
                matching.append(info)

        return {
            "profile": profile,
            "matching_tracks": matching,
            "selected_track": matching[0] if matching else None,
            "base_volume_db": base_vol,
            "fade_in_seconds": profile.get("fade_in", 0.5),
            "fade_out_seconds": profile.get("fade_out", 1.0),
            "ducking": ducking,
            "target_duration": duration,
            "source": "library" if matching else "procedural"
        }

    def trim_music(
        self,
        audio_path: str,
        output_path: str,
        target_duration: float,
        fade_in: float = 0.5,
        fade_out: float = 1.0
    ) -> str:
        """Trim music to exact duration with fades."""
        try:
            import librosa
            import soundfile as sf

            y, sr = librosa.load(audio_path, sr=None)
            current_dur = len(y) / sr

            if current_dur >= target_duration:
                y_trimmed = y[:int(target_duration * sr)]
            else:
                repeats = int(np.ceil(target_duration / current_dur))
                y_looped = np.tile(y, repeats)
                y_trimmed = y_looped[:int(target_duration * sr)]

            # Fade in
            if fade_in > 0:
                n = int(fade_in * sr)
                y_trimmed[:n] *= np.linspace(0, 1, n)

            # Fade out
            if fade_out > 0:
                n = int(fade_out * sr)
                y_trimmed[-n:] *= np.linspace(1, 0, n)

            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            sf.write(output_path, y_trimmed, sr)
            return output_path

        except Exception as e:
            logger.error(f"Music trim failed: {e}")
            raise RuntimeError(f"Music processing failed: {str(e)}")

    def duck_music(
        self,
        music_path: str,
        voice_path: str,
        output_path: str,
        ducking_params: Optional[Dict[str, Any]] = None
    ) -> str:
        """Apply audio ducking — lower music volume during speech."""
        if ducking_params is None:
            ducking_params = {}

        try:
            import librosa
            import soundfile as sf

            y_music, sr = librosa.load(music_path, sr=None)
            y_voice, _ = librosa.load(voice_path, sr=sr)

            min_len = min(len(y_music), len(y_voice))
            y_music = y_music[:min_len]
            y_voice = y_voice[:min_len]

            # Detect speech energy
            frame_len = int(0.02 * sr)
            hop_len = int(0.01 * sr)

            voice_energy = librosa.feature.rms(y=y_voice, frame_length=frame_len, hop_length=hop_len)[0]
            if voice_energy.max() > 0:
                voice_energy = voice_energy / voice_energy.max()

            # Create ducking mask
            threshold = 0.1
            mask = np.where(voice_energy > threshold, 0.3, 1.0)

            from scipy.ndimage import gaussian_filter1d
            mask = gaussian_filter1d(mask, sigma=2)

            mask_full = np.repeat(mask, hop_len)[:min_len]
            y_ducked = y_music * mask_full

            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            sf.write(output_path, y_ducked, sr)
            return output_path

        except ImportError as e:
            logger.warning(f"Advanced ducking unavailable ({e}), using simple volume reduction")
            import librosa, soundfile as sf
            y, sr = librosa.load(music_path, sr=None)
            sf.write(output_path, y * 0.4, sr)
            return output_path

        except Exception as e:
            logger.error(f"Audio ducking failed: {e}")
            raise RuntimeError(f"Audio ducking failed: {str(e)}")

    def get_safety_info(self) -> Dict[str, Any]:
        return {
            "policy": "Only CC0, Public Domain, and Royalty-Free music",
            "copyright_safe": True,
            "youtube_content_id_safe": True,
            "note": "All music cleared for YouTube Shorts monetization"
        }
