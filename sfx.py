import logging
import os
from typing import List, Dict, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


class SFXService:
    """
    Sound Effects Service.
    Automatically analyzes, selects, and places SFX.
    Uses CC0 library files or procedural generation.
    """

    SFX_CATEGORIES = {
        "whoosh": {
            "description": "Fast movement, transition, camera pan",
            "triggers": ["movement", "transition", "camera pan", "zoom", "quick cut"],
            "emotions": ["energetic", "dynamic", "action"],
            "volume_db": -12
        },
        "hit": {
            "description": "Impact, punch, emphasis",
            "triggers": ["impact", "punch", "emphasis", "important point", "reveal"],
            "emotions": ["dramatic", "intense", "shocking"],
            "volume_db": -10
        },
        "boom": {
            "description": "Deep impact, big reveal",
            "triggers": ["explosion", "big reveal", "shocking fact", "epic moment"],
            "emotions": ["epic", "dramatic", "shocking", "horror"],
            "volume_db": -8
        },
        "click": {
            "description": "UI sound, selection",
            "triggers": ["click", "select", "button", "choice", "list item"],
            "emotions": ["informative", "educational", "tech"],
            "volume_db": -15
        },
        "impact": {
            "description": "Heavy impact, emphasis",
            "triggers": ["heavy", "important", "key point", "emphasis"],
            "emotions": ["serious", "dramatic", "important"],
            "volume_db": -12
        },
        "transition": {
            "description": "Scene transition sound",
            "triggers": ["scene change", "transition", "new topic"],
            "emotions": ["neutral", "flow"],
            "volume_db": -14
        },
        "ambient": {
            "description": "Background atmosphere",
            "triggers": ["atmosphere", "setting", "mood"],
            "emotions": ["horror", "mysterious", "calm", "epic"],
            "volume_db": -24
        },
        "riser": {
            "description": "Building tension",
            "triggers": ["build up", "tension", "before reveal", "anticipation"],
            "emotions": ["suspense", "anticipation", "epic", "horror"],
            "volume_db": -14
        },
        "pop": {
            "description": "Light emphasis, playful",
            "triggers": ["funny", "cute", "playful", "light emphasis"],
            "emotions": ["funny", "playful", "light"],
            "volume_db": -13
        },
        "swoosh": {
            "description": "Smooth movement",
            "triggers": ["smooth transition", "glide", "elegant movement"],
            "emotions": ["luxury", "elegant", "smooth"],
            "volume_db": -15
        },
        "thud": {
            "description": "Heavy fall",
            "triggers": ["fall", "drop", "heavy impact"],
            "emotions": ["dramatic", "shocking"],
            "volume_db": -11
        },
        "whisper": {
            "description": "Spooky whisper",
            "triggers": ["horror", "scary", "whisper", "ghost"],
            "emotions": ["horror", "mysterious", "scary"],
            "volume_db": -16
        }
    }

    def __init__(self):
        self._sfx_library = {}
        self._scan_library()

    def _scan_library(self) -> None:
        """Scan SFX library directory."""
        sfx_dir = os.path.join(
            os.path.dirname(__file__),
            "..", "..", "assets", "sfx"
        )
        if os.path.exists(sfx_dir):
            for category in self.SFX_CATEGORIES:
                cat_dir = os.path.join(sfx_dir, category)
                if os.path.exists(cat_dir):
                    self._sfx_library[category] = [
                        os.path.join(cat_dir, f)
                        for f in os.listdir(cat_dir)
                        if f.endswith((".wav", ".mp3", ".ogg"))
                    ]
            total = sum(len(v) for v in self._sfx_library.values())
            logger.info(f"SFX library: {total} sounds in {len(self._sfx_library)} categories")

    def analyze_sfx_need(
        self,
        scenes: List[Dict[str, Any]],
        niche: str = "",
        content_type: str = "",
        pacing: str = "medium"
    ) -> List[Dict[str, Any]]:
        """Analyze scenes and suggest SFX placements."""
        suggestions = []
        niche_lower = niche.lower()

        for i, scene in enumerate(scenes):
            scene_num = scene.get("Scene Number", i + 1)
            emotion = str(scene.get("Emotion", "")).lower()
            visual = str(scene.get("Visual Description", "")).lower()
            transition = str(scene.get("Transition", "Cut")).lower()
            duration = float(scene.get("Duration", 3))

            # Scene transition
            if i > 0 and transition in ["swipe", "glitch", "zoom"]:
                suggestions.append({
                    "type": "whoosh",
                    "scene_number": scene_num,
                    "scene_index": i,
                    "timing": "start",
                    "offset": 0.0,
                    "reason": f"Transition: {transition}"
                })
            elif i > 0 and transition == "flash":
                suggestions.append({
                    "type": "hit",
                    "scene_number": scene_num,
                    "scene_index": i,
                    "timing": "start",
                    "offset": 0.0,
                    "reason": "Flash transition"
                })

            # Emotion-based
            if any(e in emotion for e in ["horror", "scary", "spooky"]):
                suggestions.append({
                    "type": "ambient",
                    "scene_number": scene_num,
                    "scene_index": i,
                    "timing": "throughout",
                    "offset": 0.0,
                    "reason": f"Horror emotion"
                })
            if any(e in emotion for e in ["dramatic", "epic", "shocking"]):
                suggestions.append({
                    "type": "riser",
                    "scene_number": scene_num,
                    "scene_index": i,
                    "timing": "build_up",
                    "offset": max(0, duration - 1.0),
                    "reason": f"Dramatic emotion"
                })
            if any(e in emotion for e in ["funny", "playful", "comedic"]):
                suggestions.append({
                    "type": "pop",
                    "scene_number": scene_num,
                    "scene_index": i,
                    "timing": "emphasis",
                    "offset": duration * 0.5,
                    "reason": f"Funny emotion"
                })
            if any(e in emotion for e in ["luxury", "elegant", "sophisticated"]):
                suggestions.append({
                    "type": "swoosh",
                    "scene_number": scene_num,
                    "scene_index": i,
                    "timing": "start",
                    "offset": 0.1,
                    "reason": f"Luxury emotion"
                })

            # Visual trigger-based
            for sfx_type, info in self.SFX_CATEGORIES.items():
                for trigger in info["triggers"]:
                    if trigger in visual:
                        suggestions.append({
                            "type": sfx_type,
                            "scene_number": scene_num,
                            "scene_index": i,
                            "timing": "auto",
                            "offset": duration * 0.3,
                            "reason": f"Visual trigger: '{trigger}'"
                        })
                        break

            # Niche-based
            if "horror" in niche_lower or "true crime" in niche_lower:
                if i == 0:
                    suggestions.append({
                        "type": "ambient",
                        "scene_number": scene_num,
                        "scene_index": i,
                        "timing": "throughout",
                        "offset": 0.0,
                        "reason": "Horror/crime atmosphere"
                    })

            # Final scene emphasis
            if i == len(scenes) - 1 and any(k in niche_lower for k in ["motivation", "sports", "epic"]):
                suggestions.append({
                    "type": "impact",
                    "scene_number": scene_num,
                    "scene_index": i,
                    "timing": "end",
                    "offset": max(0, duration - 0.3),
                    "reason": "Final scene emphasis"
                })

        logger.info(f"SFX analysis: {len(suggestions)} suggestions for {len(scenes)} scenes")
        return suggestions

    def select_sfx(self, sfx_type: str) -> Optional[str]:
        """Select SFX file from library."""
        if sfx_type in self._sfx_library and self._sfx_library[sfx_type]:
            import random
            return random.choice(self._sfx_library[sfx_type])
        return None

    def generate_procedural_sfx(
        self,
        sfx_type: str,
        output_path: str,
        duration: float = 0.5
    ) -> Optional[str]:
        """Generate simple procedural SFX when library unavailable."""
        try:
            import soundfile as sf

            sr = 44100
            t = np.linspace(0, duration, int(sr * duration), endpoint=False)

            if sfx_type == "whoosh":
                noise = np.random.randn(len(t))
                freq = np.linspace(200, 2000, len(t))
                carrier = np.sin(2 * np.pi * freq * t)
                y = noise * carrier * np.exp(-3 * t)
            elif sfx_type == "pop":
                y = np.sin(2 * np.pi * 800 * t) * np.exp(-20 * t)
            elif sfx_type == "click":
                y = np.random.randn(len(t)) * np.exp(-50 * t)
            elif sfx_type == "riser":
                freq = np.linspace(100, 1000, len(t))
                y = np.sin(2 * np.pi * freq * t) * np.linspace(0, 1, len(t))
                y += 0.5 * np.sin(2 * np.pi * freq * 2 * t) * np.linspace(0, 0.5, len(t))
            elif sfx_type == "boom":
                freq = 60
                env = np.exp(-2 * t)
                y = np.sin(2 * np.pi * freq * t) * env
                y += 0.3 * np.sin(2 * np.pi * freq * 1.5 * t) * env
            elif sfx_type == "hit":
                freq = 150
                y = np.sin(2 * np.pi * freq * t) * np.exp(-15 * t)
                y += 0.5 * np.random.randn(len(t)) * np.exp(-25 * t)
            elif sfx_type == "swoosh":
                noise = np.random.randn(len(t))
                freq = np.linspace(800, 300, len(t))
                carrier = np.sin(2 * np.pi * freq * t)
                y = noise * carrier * np.exp(-2 * t)
            else:
                y = np.random.randn(len(t)) * np.exp(-30 * t)

            y = y / np.max(np.abs(y)) * 0.5

            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            sf.write(output_path, y, sr)
            return output_path

        except Exception as e:
            logger.error(f"Procedural SFX failed: {e}")
            return None

    def place_sfx(
        self,
        base_audio_path: str,
        sfx_placements: List[Dict[str, Any]],
        output_path: str
    ) -> Dict[str, Any]:
        """Place SFX at specific timing points in base audio."""
        if not sfx_placements:
            return {"path": base_audio_path, "sfx_added": 0, "sfx_skipped": 0}

        try:
            import librosa
            import soundfile as sf

            y_base, sr = librosa.load(base_audio_path, sr=None)
            added = 0
            skipped = 0

            for p in sfx_placements:
                sfx_type = p.get("type")
                timing = p.get("timing_seconds", 0.0)

                sfx_path = self.select_sfx(sfx_type)
                if sfx_path is None:
                    proc_dir = os.path.join(os.path.dirname(output_path), "sfx")
                    os.makedirs(proc_dir, exist_ok=True)
                    proc_path = os.path.join(proc_dir, f"{sfx_type}_{timing:.1f}s.wav")
                    sfx_path = self.generate_procedural_sfx(sfx_type, proc_path)

                if sfx_path is None or not os.path.exists(sfx_path):
                    skipped += 1
                    continue

                y_sfx, _ = librosa.load(sfx_path, sr=sr)

                start = int(timing * sr)
                if start >= len(y_base):
                    skipped += 1
                    continue

                info = self.SFX_CATEGORIES.get(sfx_type, {})
                target_db = info.get("volume_db", -12)
                current_db = librosa.amplitude_to_db(np.abs(y_sfx)).mean()
                gain = 10 ** ((target_db - current_db) / 20)
                y_sfx = y_sfx * gain

                end = min(start + len(y_sfx), len(y_base))
                y_base[start:end] += y_sfx[:end - start] * 0.7
                added += 1

            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
            sf.write(output_path, y_base, sr)

            return {"path": output_path, "sfx_added": added, "sfx_skipped": skipped}

        except Exception as e:
            logger.error(f"SFX placement failed: {e}")
            return {"path": base_audio_path, "sfx_added": 0, "sfx_skipped": len(sfx_placements)}

    def get_safety_info(self) -> Dict[str, Any]:
        return {
            "policy": "Only CC0, Public Domain, and Royalty-Free SFX",
            "copyright_safe": True,
            "youtube_content_id_safe": True
        }
