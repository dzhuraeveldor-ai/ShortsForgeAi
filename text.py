import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)


class TextService:
    """
    Service for generating all text content using AI.
    Falls back gracefully if no AI model is available.

    Features:
    - Ideas generation
    - Hooks generation
    - Script generation
    - Scene breakdown
    - Character reference
    - Image/video prompts
    - SEO: titles, description, hashtags, keywords, CTA
    - Analysis and improvement suggestions
    """

    def __init__(self):
        self._model_available = None
        self._ollama = None

    def _check_ollama(self) -> bool:
        """Check if Ollama is available for text generation."""
        if self._model_available is not None:
            return self._model_available

        try:
            import ollama
            # Check if Ollama is running
            models = ollama.list()
            if models and models.get("models"):
                self._ollama = ollama
                self._model_available = True
                logger.info(f"Ollama available. Models: {[m['name'] for m in models.get('models', [])]}")
                return True
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")

        self._model_available = False
        return False

    def is_available(self) -> bool:
        """Public method to check text generation availability."""
        return self._check_ollama()

    def _generate(self, prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """Internal generation using Ollama."""
        if not self._check_ollama():
            raise RuntimeError("Text generation model not available")

        try:
            response = self._ollama.generate(
                model="qwen2:7b",
                prompt=prompt,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    "top_p": 0.9
                }
            )
            return response.get("response", "").strip()
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise RuntimeError(f"Text generation failed: {str(e)}")

    # ============================================================
    # IDEAS
    # ============================================================
    def generate_ideas(self, niche: str, content_type: str, count: int = 5) -> List[str]:
        """Generate creative content ideas."""
        prompt = f"""Generate {count} creative YouTube Shorts ideas for niche: {niche}, content type: {content_type}.

Requirements:
- Each idea should be 1-2 sentences
- Hooky and attention-grabbing
- Suitable for 15-60 second vertical videos
- Diverse angles and approaches
- American English, conversational tone

Return ONLY the list of ideas, numbered 1-{count}, no extra text."""

        try:
            result = self._generate(prompt, max_tokens=1500, temperature=0.8)
            # Parse numbered list
            ideas = []
            for line in result.strip().split("\n"):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") or line.startswith(f"{i})") for i in range(1, count + 1)):
                    # Remove numbering
                    idea = line.split(".", 1)[-1].split(")", 1)[-1].strip()
                    if idea:
                        ideas.append(idea)
            return ideas[:count] if ideas else [result[:200]] * count
        except Exception as e:
            logger.warning(f"Idea generation failed: {e}")
            return [f"Exploring the fascinating world of {niche} — you won't believe this!"] * count

    # ============================================================
    # HOOKS
    # ============================================================
    def generate_hooks(self, niche: str, content_type: str, count: int = 5) -> List[str]:
        """Generate attention-grabbing opening hooks."""
        prompt = f"""Generate {count} powerful opening hooks for YouTube Shorts about {niche} ({content_type}).

Requirements:
- Each hook is 1 sentence only
- Stops the scroll immediately
- Creates curiosity, urgency, or surprise
- Perfect for the first 3 seconds of a Short
- American English

Return ONLY the hooks, numbered 1-{count}."""

        try:
            result = self._generate(prompt, max_tokens=800, temperature=0.9)
            hooks = []
            for line in result.strip().split("\n"):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") or line.startswith(f"{i})") for i in range(1, count + 1)):
                    hook = line.split(".", 1)[-1].split(")", 1)[-1].strip().strip('"').strip("'")
                    if hook:
                        hooks.append(hook)
            return hooks[:count] if hooks else [f"You won't believe what happened with {niche}!"] * count
        except Exception as e:
            logger.warning(f"Hook generation failed: {e}")
            return [f"You won't believe this about {niche}!"] * count

    # ============================================================
    # SCRIPT
    # ============================================================
    def generate_script(
        self,
        niche: str,
        content_type: str,
        hook: str = "",
        idea: str = "",
        duration: int = 30,
        language: str = "American English"
    ) -> Dict[str, str]:
        """Generate complete script structure."""
        wpm = 150  # words per minute
        target_words = int((duration / 60) * wpm)

        prompt = f"""Write a complete YouTube Shorts script.

Niche: {niche}
Content Type: {content_type}
Hook: {hook or 'Generate a powerful hook'}
Idea: {idea or 'Make it engaging and surprising'}
Target Duration: {duration} seconds (~{target_words} words total)
Language: {language}

Structure the script with EXACTLY these sections:
HOOK: (first 3 seconds, stops the scroll)
INTRO: (brief setup)
MAIN STORY: (core content)
PAYOFF: (surprise twist or key takeaway)
CTA: (call to action — like, subscribe)

Write in conversational American English, as if speaking directly to camera.
Be engaging, energetic, and concise."""

        try:
            result = self._generate(prompt, max_tokens=2000, temperature=0.75)

            # Parse sections
            script = {
                "HOOK": "",
                "INTRO": "",
                "MAIN STORY": "",
                "PAYOFF": "",
                "CTA": ""
            }

            current_section = None
            for line in result.split("\n"):
                line = line.strip()
                upper_line = line.upper()

                for section in script:
                    if upper_line.startswith(section + ":") or upper_line.startswith(section + " "):
                        current_section = section
                        content = line.split(":", 1)[-1].strip()
                        if content:
                            script[current_section] = content
                        break
                else:
                    if current_section and line:
                        script[current_section] += " " + line if script[current_section] else line

            # Clean up
            for key in script:
                script[key] = script[key].strip()

            # Ensure we have content
            if not script["HOOK"]:
                script["HOOK"] = hook or f"Did you know this about {niche}?"
            if not script["MAIN STORY"]:
                script["MAIN STORY"] = result[:500]

            return script

        except Exception as e:
            logger.warning(f"Script generation failed: {e}")
            return {
                "HOOK": hook or f"Did you know this about {niche}?",
                "INTRO": "Today we explore something truly amazing.",
                "MAIN STORY": f"This is the story of {niche}. Most people have no idea how fascinating this really is.",
                "PAYOFF": "And that's the truth you need to know.",
                "CTA": "Like and subscribe for more!"
            }

    # ============================================================
    # SCENE BREAKDOWN
    # ============================================================
    def generate_scene_breakdown(
        self,
        script: Dict[str, str],
        duration: int,
        visual_style: str,
        niche: str
    ) -> List[Dict[str, Any]]:
        """Break script into individual scenes with visual descriptions."""
        full_script = " ".join(str(v) for v in script.values())
        num_scenes = max(2, min(6, duration // 8))

        prompt = f"""Break this YouTube Shorts script into {num_scenes} visual scenes.

Script: {full_script[:800]}
Niche: {niche}
Visual Style: {visual_style}
Total Duration: {duration} seconds

For EACH scene provide:
Scene Number: (1-{num_scenes})
Duration: (seconds per scene)
Narration: (exact words spoken)
Visual Description: (what appears on screen, detailed)
Camera Movement: (static, slow_zoom_in, slow_zoom_out, pan_left, pan_right, handheld)
Lighting: (cinematic, bright, dark, dramatic, etc.)
Transition: (cut, fade, zoom, swipe)
Emotion: (neutral, informative, dramatic, funny, horror, epic, etc.)

Make scenes flow logically. Total duration should equal {duration}s."""

        try:
            result = self._generate(prompt, max_tokens=2500, temperature=0.7)

            # Simple parsing — split by scene markers
            scenes = []
            current_scene = {}

            for line in result.split("\n"):
                line = line.strip()
                if not line:
                    continue

                upper = line.upper()
                if "SCENE" in upper and any(c.isdigit() for c in line):
                    if current_scene:
                        scenes.append(current_scene)
                    current_scene = {}
                    continue

                for field in ["Scene Number", "Duration", "Narration", "Visual Description",
                              "Camera Movement", "Lighting", "Transition", "Emotion"]:
                    if line.startswith(field + ":"):
                        key = field
                        value = line.split(":", 1)[-1].strip()
                        current_scene[key] = value
                        break

            if current_scene:
                scenes.append(current_scene)

            if scenes:
                return scenes

        except Exception as e:
            logger.warning(f"Scene breakdown failed: {e}")

        # Fallback
        half = max(2, duration // 2)
        return [
            {
                "Scene Number": 1,
                "Duration": half,
                "Narration": script.get("HOOK", "") + " " + script.get("INTRO", ""),
                "Visual Description": f"Introduction to {niche}",
                "Camera Movement": "slow_zoom_in",
                "Lighting": "cinematic",
                "Transition": "none",
                "Emotion": "neutral"
            },
            {
                "Scene Number": 2,
                "Duration": duration - half,
                "Narration": script.get("MAIN STORY", "") + " " + script.get("PAYOFF", ""),
                "Visual Description": f"Main content about {niche}",
                "Camera Movement": "static",
                "Lighting": "bright",
                "Transition": "fade",
                "Emotion": "informative"
            }
        ]

    # ============================================================
    # CHARACTER REFERENCE
    # ============================================================
    def generate_character_reference(
        self,
        script: Dict[str, str],
        niche: str,
        visual_style: str
    ) -> Optional[Dict[str, str]]:
        """Generate character description for visual consistency across scenes."""
        prompt = f"""Describe a consistent character/host appearance for this YouTube Short.

Niche: {niche}
Visual Style: {visual_style}
Script tone: {script.get('HOOK', '')[:100]}

Provide:
Full Description: (complete visual description for AI image generation)
Hair:
Outfit:
Setting:
Overall Vibe:

Make it specific enough for consistent image generation."""

        try:
            result = self._generate(prompt, max_tokens=800, temperature=0.7)
            ref = {"Full Description": result}

            for line in result.split("\n"):
                line = line.strip()
                for field in ["Hair", "Outfit", "Setting", "Overall Vibe"]:
                    if line.startswith(field + ":"):
                        ref[field] = line.split(":", 1)[-1].strip()

            return ref
        except Exception as e:
            logger.warning(f"Character reference failed: {e}")
            return None

    # ============================================================
    # IMAGE PROMPT
    # ============================================================
    def generate_image_prompt(
        self,
        scene: Dict[str, Any],
        visual_style: str,
        character_ref: Optional[Dict[str, str]] = None
    ) -> Dict[str, str]:
        """Generate detailed positive and negative prompts for image generation."""
        visual = scene.get("Visual Description", "")
        camera = scene.get("Camera Movement", "static")
        lighting = scene.get("Lighting", "cinematic")
        emotion = scene.get("Emotion", "neutral")

        char_desc = character_ref.get("Full Description", "") if character_ref else ""

        positive = (
            f"{char_desc}, {visual}, "
            f"{visual_style} style, "
            f"camera: {camera}, "
            f"lighting: {lighting}, "
            f"mood: {emotion}, "
            f"vertical 9:16 composition, "
            f"high quality, detailed, sharp focus, cinematic"
        )

        negative = (
            "ugly, blurry, low quality, distorted, deformed, "
            "extra limbs, bad anatomy, watermark, text, signature, "
            "cropped, out of frame, grainy, noisy"
        )

        return {"positive": positive, "negative": negative}

    # ============================================================
    # VIDEO PROMPT
    # ============================================================
    def generate_video_prompt(
        self,
        scene: Dict[str, Any],
        visual_style: str,
        character_ref: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate prompt for video generation."""
        visual = scene.get("Visual Description", "")
        camera = scene.get("Camera Movement", "static")
        emotion = scene.get("Emotion", "neutral")
        char_desc = character_ref.get("Full Description", "") if character_ref else ""

        return (
            f"{char_desc}, {visual}, "
            f"{visual_style} style, "
            f"camera movement: {camera}, "
            f"emotion: {emotion}, "
            f"smooth motion, cinematic, high quality, vertical 9:16"
        )

    # ============================================================
    # SEO: TITLES
    # ============================================================
    def generate_titles(self, script: Dict[str, str], niche: str, count: int = 5) -> List[str]:
        """Generate YouTube Shorts titles."""
        hook = script.get("HOOK", "")[:100]
        prompt = f"""Generate {count} YouTube Shorts titles.

Niche: {niche}
Hook: {hook}

Requirements:
- 50-70 characters maximum
- Include #Shorts hashtag
- Clickable, curiosity-inducing
- Use numbers, questions, or surprises
- American English

Return ONLY the titles, numbered 1-{count}."""

        try:
            result = self._generate(prompt, max_tokens=1000, temperature=0.85)
            titles = []
            for line in result.strip().split("\n"):
                line = line.strip()
                if line and any(line.startswith(f"{i}.") or line.startswith(f"{i})") for i in range(1, count + 1)):
                    title = line.split(".", 1)[-1].split(")", 1)[-1].strip().strip('"')
                    if title:
                        if "#shorts" not in title.lower():
                            title += " #Shorts"
                        titles.append(title[:100])
            return titles[:count] if titles else [f"Amazing {niche}! #Shorts"] * count
        except Exception as e:
            logger.warning(f"Title generation failed: {e}")
            return [f"Fascinating {niche} facts! #Shorts"] * count

    # ============================================================
    # SEO: DESCRIPTION
    # ============================================================
    def generate_description(self, script: Dict[str, str], niche: str, titles: List[str]) -> str:
        """Generate YouTube video description."""
        main = script.get("MAIN STORY", "")[:300]
        title = titles[0] if titles else f"About {niche}"

        prompt = f"""Write a YouTube Shorts description.

Title: {title}
Niche: {niche}
Content: {main}

Requirements:
- 2-3 paragraphs
- Include relevant keywords naturally
- End with a call to action
- Include relevant hashtags at the bottom
- American English, friendly tone"""

        try:
            return self._generate(prompt, max_tokens=1000, temperature=0.7)
        except Exception as e:
            logger.warning(f"Description generation failed: {e}")
            return (
                f"Check out this amazing content about {niche}!\n\n"
                f"Don't forget to LIKE and SUBSCRIBE for more!\n\n"
                f"#shorts #youtubeshorts #{niche.replace(' ', '')}"
            )

    # ============================================================
    # SEO: HASHTAGS
    # ============================================================
    def generate_hashtags(self, script: Dict[str, str], niche: str, count: int = 15) -> List[str]:
        """Generate relevant hashtags."""
        content = " ".join(str(v) for v in script.values())[:300]
        prompt = f"""Generate {count} relevant YouTube Shorts hashtags.

Niche: {niche}
Content: {content}

Mix of:
- Broad hashtags (#shorts, #viral)
- Niche-specific hashtags
- Trending format hashtags

Return ONLY the hashtags, space-separated, including # symbol."""

        try:
            result = self._generate(prompt, max_tokens=500, temperature=0.7)
            tags = [t.strip() for t in result.split() if t.startswith("#")]
            unique = list(dict.fromkeys(tags))  # Remove duplicates
            return unique[:count]
        except Exception as e:
            logger.warning(f"Hashtag generation failed: {e}")
            return ["#shorts", "#youtubeshorts", "#viral", "#fyp", "#trending"]

    # ============================================================
    # SEO: KEYWORDS
    # ============================================================
    def generate_keywords(self, script: Dict[str, str], niche: str, count: int = 10) -> List[str]:
        """Generate SEO keywords."""
        content = " ".join(str(v) for v in script.values())[:300]
        prompt = f"""Generate {count} SEO keywords for a YouTube Short.

Niche: {niche}
Content: {content}

Single words or short phrases. Comma-separated."""

        try:
            result = self._generate(prompt, max_tokens=300, temperature=0.6)
            keywords = [k.strip() for k in result.replace("\n", ",").split(",") if k.strip()]
            return keywords[:count]
        except Exception as e:
            logger.warning(f"Keyword generation failed: {e}")
            return [niche, "shorts", "viral", "trending", "amazing"]

    # ============================================================
    # CTA
    # ============================================================
    def generate_cta(self) -> str:
        """Generate call to action."""
        prompt = """Write a strong YouTube Shorts call to action (spoken aloud).
- 1-2 sentences
- Energetic, friendly
- Ask to LIKE and SUBSCRIBE
- American English
- Conversational tone"""

        try:
            return self._generate(prompt, max_tokens=200, temperature=0.8)
        except Exception as e:
            logger.warning(f"CTA generation failed: {e}")
            return "Like and subscribe for more amazing content every single day!"

    # ============================================================
    # ANALYSIS
    # ============================================================
    def analyze_short(self, script: Dict[str, str], niche: str) -> Dict[str, Any]:
        """Analyze script quality and suggest improvements."""
        full = " ".join(str(v) for v in script.values())
        word_count = len(full.split())

        return {
            "word_count": word_count,
            "estimated_duration_seconds": round(word_count / 150 * 60),
            "hook_strength": "Good" if len(script.get("HOOK", "")) > 20 else "Could be stronger",
            "cta_present": bool(script.get("CTA", "")),
            "structure_complete": all(script.get(k) for k in ["HOOK", "MAIN STORY", "CTA"]),
            "suggestions": [
                "Make the first 3 seconds even more hooky",
                "Add a surprise element in the middle",
                "End with a clear question to boost engagement"
            ]
        }

    # ============================================================
    # IMPROVE
    # ============================================================
    def improve_short(self, script: Dict[str, str], niche: str) -> Dict[str, str]:
        """Improve an existing script."""
        prompt = f"""Improve this YouTube Shorts script.

Niche: {niche}

Current script:
HOOK: {script.get('HOOK', '')}
INTRO: {script.get('INTRO', '')}
MAIN STORY: {script.get('MAIN STORY', '')}
PAYOFF: {script.get('PAYOFF', '')}
CTA: {script.get('CTA', '')}

Make it:
- More hooky and engaging
- Tighter and more concise
- Better flow
- More conversational
- Keep the same structure (HOOK, INTRO, MAIN STORY, PAYOFF, CTA)"""

        try:
            result = self._generate(prompt, max_tokens=1500, temperature=0.75)
            improved = dict(script)

            for line in result.split("\n"):
                line = line.strip()
                upper = line.upper()
                for section in ["HOOK", "INTRO", "MAIN STORY", "PAYOFF", "CTA"]:
                    if upper.startswith(section + ":"):
                        content = line.split(":", 1)[-1].strip()
                        if content:
                            improved[section] = content
                        break

            return improved
        except Exception as e:
            logger.warning(f"Script improvement failed: {e}")
            return script
