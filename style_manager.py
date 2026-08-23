"""
Style Manager — converts user-selected visual styles into
detailed positive/negative prompts, lighting, camera settings.
"""

from typing import Dict, Any, List, Optional


class StyleManager:
    """Manages visual style conversion for image/video generation."""

    STYLES = {
        "realistic": {
            "label": "📸 Realistic",
            "positive": [
                "photorealistic", "ultra detailed", "8k", "high resolution",
                "sharp focus", "professional photography", "natural lighting",
                "hyperrealistic", "intricate details", "lifelike"
            ],
            "negative": [
                "cartoon", "anime", "drawing", "painting", "illustration",
                "blurry", "low quality", "distorted", "ugly", "deformed",
                "extra limbs", "bad anatomy", "watermark", "text"
            ],
            "lighting": "natural, soft, cinematic lighting",
            "camera": "professional DSLR, 50mm lens, shallow depth of field",
            "composition": "rule of thirds, balanced composition"
        },
        "cinematic": {
            "label": "🎬 Cinematic",
            "positive": [
                "cinematic", "film still", "movie shot", "dramatic lighting",
                "anamorphic lens", "cinematography", "film grain",
                "color graded", "moody atmosphere", "shallow depth of field"
            ],
            "negative": [
                "cartoon", "anime", "overexposed", "flat lighting",
                "amateur", "blurry", "low quality", "distorted", "watermark"
            ],
            "lighting": "dramatic, high contrast, volumetric lighting, god rays",
            "camera": "35mm anamorphic lens, cinematic composition",
            "composition": "dynamic framing, leading lines"
        },
        "3d": {
            "label": "🧊 3D",
            "positive": [
                "3d render", "octane render", "unreal engine 5", "pixar style",
                "ray tracing", "global illumination", "high poly",
                "pbr materials", "soft shadows", "ambient occlusion"
            ],
            "negative": [
                "2d", "flat", "cartoon", "drawing", "painting",
                "low poly", "pixelated", "blurry", "low quality"
            ],
            "lighting": "studio lighting, softbox, rim lighting",
            "camera": "3d camera, cinematic angle, depth of field",
            "composition": "centered, clean background"
        },
        "2d": {
            "label": "🎨 2D",
            "positive": [
                "2d art", "digital painting", "concept art", "matte painting",
                "detailed background", "rich colors", "artistic",
                "painterly", "brush strokes", "illustration"
            ],
            "negative": [
                "3d", "photorealistic", "photography", "blurry",
                "low quality", "distorted", "amateur"
            ],
            "lighting": "artistic lighting, color harmony",
            "camera": "2d composition, flat perspective",
            "composition": "artistic framing, layered"
        },
        "cartoon": {
            "label": "✏️ Cartoon",
            "positive": [
                "cartoon style", "animated", "clean lines", "cel shaded",
                "vibrant colors", "simple design", "expressive",
                "comic style", "playful", "whimsical"
            ],
            "negative": [
                "photorealistic", "3d", "gritty", "dark", "horror",
                "blurry", "low quality", "complex background"
            ],
            "lighting": "bright, even lighting, vibrant colors",
            "camera": "flat, 2d animation style",
            "composition": "simple, clear, focused on subject"
        },
        "anime": {
            "label": "🇯🇵 Anime",
            "positive": [
                "anime style", "manga", "studio ghibli", "vibrant",
                "expressive eyes", "beautiful colors", "detailed",
                "japanese animation", "cel shaded", "artistic"
            ],
            "negative": [
                "photorealistic", "3d", "ugly", "deformed",
                "western cartoon", "blurry", "low quality"
            ],
            "lighting": "soft, colorful, atmospheric",
            "camera": "dynamic anime angles, expressive",
            "composition": "dynamic, emotional framing"
        },
        "game": {
            "label": "🎮 Game Style",
            "positive": [
                "video game screenshot", "game art", "unreal engine",
                "detailed environment", "game asset", "stylized",
                "high quality textures", "dynamic lighting"
            ],
            "negative": [
                "photorealistic", "photography", "blurry",
                "low quality", "amateur", "ui elements", "hud"
            ],
            "lighting": "dynamic game lighting, real-time",
            "camera": "third person or first person game view",
            "composition": "action-oriented"
        },
        "scifi": {
            "label": "🌌 Sci-Fi",
            "positive": [
                "sci-fi", "futuristic", "cyberpunk", "space",
                "neon lights", "advanced technology", "spaceship",
                "holographic", "high tech", "dystopian"
            ],
            "negative": [
                "medieval", "fantasy", "vintage", "old fashioned",
                "blurry", "low quality", "distorted"
            ],
            "lighting": "neon, volumetric, futuristic, moody",
            "camera": "wide angle, futuristic perspective",
            "composition": "grand scale, epic"
        },
        "dark_horror": {
            "label": "👻 Dark Horror",
            "positive": [
                "horror", "dark", "creepy", "eerie", "gloomy",
                "shadowy", "sinister", "macabre", "gothic",
                "tense atmosphere", "frightening"
            ],
            "negative": [
                "bright", "cheerful", "colorful", "cartoon",
                "happy", "cute", "blurry", "low quality"
            ],
            "lighting": "dark, moody, low key, shadows, moonlight",
            "camera": "unsettling angles, claustrophobic",
            "composition": "tense, mysterious"
        },
        "illustration": {
            "label": "🖼 Illustration",
            "positive": [
                "illustration", "artistic", "hand drawn", "stylized",
                "creative", "unique style", "expressive",
                "beautiful", "art", "imaginative"
            ],
            "negative": [
                "photorealistic", "photography", "3d", "blurry",
                "low quality", "amateur"
            ],
            "lighting": "artistic, creative, mood-appropriate",
            "camera": "illustration perspective",
            "composition": "creative, expressive"
        },
        "documentary": {
            "label": "📚 Documentary",
            "positive": [
                "documentary style", "authentic", "realistic",
                "journalistic", "informative", "natural",
                "genuine", "unfiltered", "historical"
            ],
            "negative": [
                "stylized", "cartoon", "fantasy", "overly dramatic",
                "blurry", "low quality", "staged"
            ],
            "lighting": "natural, available light, authentic",
            "camera": "documentary style, handheld, observational",
            "composition": "natural, unposed"
        },
        "luxury": {
            "label": "💎 Luxury",
            "positive": [
                "luxury", "elegant", "premium", "high end", "sophisticated",
                "expensive", "classy", "refined", "gold accents",
                "marble", "velvet", "crystal", "opulent"
            ],
            "negative": [
                "cheap", "poor", "tacky", "low quality", "messy",
                "worn out", "damaged", "blurry"
            ],
            "lighting": "soft, elegant, warm, premium studio lighting",
            "camera": "sleek, refined, elegant angles",
            "composition": "clean, minimalist, premium"
        },
        "stylized": {
            "label": "🎭 Stylized",
            "positive": [
                "stylized", "artistic", "unique", "creative",
                "interpretive", "non-photorealistic", "expressive",
                "bold", "distinctive", "original"
            ],
            "negative": [
                "photorealistic", "generic", "boring", "blurry",
                "low quality", "amateur"
            ],
            "lighting": "creative, stylized, mood-appropriate",
            "camera": "creative angles",
            "composition": "artistic, unique"
        },
        "fantasy": {
            "label": "🌈 Fantasy",
            "positive": [
                "fantasy", "magical", "enchanted", "mythical",
                "epic", "legendary", "dragon", "wizard", "castle",
                "mystical", "otherworldly", "dreamlike"
            ],
            "negative": [
                "sci-fi", "modern", "realistic", "ordinary",
                "blurry", "low quality", "distorted"
            ],
            "lighting": "magical, golden hour, ethereal, mystical",
            "camera": "epic, wide angle, grand",
            "composition": "epic scale, mythical"
        },
        "random": {
            "label": "🎲 Random",
            "positive": [],
            "negative": [],
            "lighting": "appropriate for the scene",
            "camera": "professional",
            "composition": "balanced"
        }
    }

    @classmethod
    def get_style_names(cls) -> List[str]:
        return list(cls.STYLES.keys())

    @classmethod
    def get_style_labels(cls) -> Dict[str, str]:
        return {k: v["label"] for k, v in cls.STYLES.items()}

    @classmethod
    def build_prompt(
        cls,
        base_prompt: str,
        style_key: str,
        aspect_ratio: str = "9:16"
    ) -> str:
        """Build complete positive image prompt with style."""
        style = cls.STYLES.get(style_key)

        if not style or style_key == "random":
            import random
            available = [k for k in cls.STYLES if k != "random"]
            style = cls.STYLES[random.choice(available)]

        parts = [base_prompt.strip()]

        if style["positive"]:
            parts.append(", ".join(style["positive"]))

        parts.append(style["lighting"])
        parts.append(style["camera"])
        parts.append(style["composition"])

        if aspect_ratio == "9:16":
            parts.append("vertical composition, portrait orientation")
        elif aspect_ratio == "16:9":
            parts.append("horizontal composition, landscape orientation")

        return ", ".join(parts)

    @classmethod
    def build_negative_prompt(cls, style_key: str) -> str:
        """Build negative prompt for style."""
        style = cls.STYLES.get(style_key, cls.STYLES["realistic"])

        base_negative = [
            "blurry", "low quality", "distorted", "deformed", "ugly",
            "bad anatomy", "extra limbs", "missing limbs", "watermark",
            "text", "signature", "cropped", "out of frame"
        ]

        all_negative = base_negative + style["negative"]
        return ", ".join(all_negative)

    @classmethod
    def get_style_info(cls, style_key: str) -> Optional[Dict[str, Any]]:
        return cls.STYLES.get(style_key)

    @classmethod
    def select_style_for_content(cls, niche: str = "", content_type: str = "") -> str:
        """Auto-select style based on niche and content type."""
        niche_lower = niche.lower() if niche else ""

        mappings = {
            "horror": "dark_horror",
            "scifi": "scifi",
            "fantasy": "fantasy",
            "anime": "anime",
            "luxury": "luxury",
            "documentary": "documentary",
            "cinematic": "cinematic",
            "gaming": "game",
            "game": "game",
            "cartoon": "cartoon",
            "funny": "cartoon",
            "education": "illustration",
            "science": "scifi",
            "space": "scifi",
            "mystery": "dark_horror",
            "history": "documentary",
            "facts": "realistic",
            "animals": "realistic",
            "travel": "cinematic",
            "food": "realistic",
            "fitness": "realistic",
            "cars": "cinematic",
            "business": "luxury",
            "programming": "scifi",
            "technology": "scifi",
            "ai": "scifi",
            "money": "luxury",
            "motivation": "cinematic",
            "sports": "cinematic",
            "movies": "cinematic",
            "true crime": "dark_horror",
            "psychology": "stylized",
            "relationships": "illustration",
            "music": "stylized"
        }

        for keyword, style in mappings.items():
            if keyword in niche_lower:
                return style

        return "realistic"
