import logging
import os
from typing import Dict, Any, Optional

from worker.config import settings

logger = logging.getLogger(__name__)


class JobStage:
    """Represents a single stage in the generation pipeline."""

    def __init__(self, name: str, display_name: str, func):
        self.name = name
        self.display_name = display_name
        self.func = func

    def function(self, results: Dict[str, Any]):
        return self.func(results)


def create_stages(project, parameters: Dict[str, Any]) -> list:
    """
    Create the complete 12-stage pipeline for a full Short generation.

    Pipeline:
    1. Generate Script
    2. Scene Breakdown
    3. Character Reference
    4. Visual Prompts
    5. Generate Images
    6. Generate Voice
    7. Generate Subtitles
    8. Prepare Music
    9. Audio Ducking
    10. Sound Effects
    11. Final Render
    12. YouTube SEO
    """
    return [
        JobStage("generate_script", "✍️ Generate Script",
                 lambda r: _stage_generate_script(project, parameters)),

        JobStage("scene_breakdown", "🎬 Scene Breakdown",
                 lambda r: _stage_scene_breakdown(project, r, parameters)),

        JobStage("character_reference", "👤 Character Reference",
                 lambda r: _stage_character_reference(project, r, parameters)),

        JobStage("visual_prompts", "🎨 Visual Prompts",
                 lambda r: _stage_visual_prompts(project, r, parameters)),

        JobStage("generate_images", "🖼 Generate Images",
                 lambda r: _stage_generate_images(project, r, parameters)),

        JobStage("generate_voice", "🎙 Generate Voice",
                 lambda r: _stage_generate_voice(project, r, parameters)),

        JobStage("generate_subtitles", "📝 Generate Subtitles",
                 lambda r: _stage_generate_subtitles(project, r, parameters)),

        JobStage("prepare_music", "🎵 Prepare Music",
                 lambda r: _stage_prepare_music(project, r, parameters)),

        JobStage("audio_ducking", "🔊 Audio Ducking",
                 lambda r: _stage_audio_ducking(project, r, parameters)),

        JobStage("sfx", "🔊 Sound Effects",
                 lambda r: _stage_sfx(project, r, parameters)),

        JobStage("final_render", "✂️ Final Render",
                 lambda r: _stage_final_render(project, r, parameters)),

        JobStage("seo", "🏷 YouTube SEO",
                 lambda r: _stage_seo(project, r, parameters))
    ]


# ============================================================
# STAGE 1: GENERATE SCRIPT
# ============================================================
def _stage_generate_script(project, parameters: Dict[str, Any]) -> Dict[str, str]:
    """Generate complete script: Hook → Intro → Main → Payoff → CTA."""
    from worker.services.text import TextService

    text_service = TextService()

    if not text_service.is_available():
        logger.warning("Text service not available — using placeholder script")
        niche = project.niche or "the topic"
        return {
            "HOOK": f"Did you know this about {niche}?",
            "INTRO": "Today we explore something truly amazing.",
            "MAIN STORY": f"This is the incredible story of {niche}. Most people have no idea how fascinating this really is.",
            "PAYOFF": "And that's the truth you need to know.",
            "CTA": "Like and subscribe for more amazing content!"
        }

    return text_service.generate_script(
        niche=project.niche or "general",
        content_type=project.content_type or "educational",
        hook=parameters.get("hook", ""),
        idea=parameters.get("idea", ""),
        duration=project.duration or 30,
        language=project.language or "American English"
    )


# ============================================================
# STAGE 2: SCENE BREAKDOWN
# ============================================================
def _stage_scene_breakdown(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> list:
    """Break script into individual scenes."""
    from worker.services.text import TextService

    script = results.get("generate_script", {})
    duration = project.duration or 30
    text_service = TextService()

    if not text_service.is_available():
        # Basic 2-scene breakdown
        half_dur = max(2, duration // 2)
        return [
            {
                "Scene Number": 1,
                "Duration": half_dur,
                "Narration": f"{script.get('HOOK', '')} {script.get('INTRO', '')}",
                "Visual Description": f"Introduction to {project.niche or 'the topic'}",
                "Camera Movement": "slow_zoom_in",
                "Lighting": "cinematic",
                "Transition": "none",
                "Emotion": "neutral"
            },
            {
                "Scene Number": 2,
                "Duration": half_dur,
                "Narration": f"{script.get('MAIN STORY', '')} {script.get('PAYOFF', '')} {script.get('CTA', '')}",
                "Visual Description": f"Main content about {project.niche or 'the topic'}",
                "Camera Movement": "static",
                "Lighting": "bright",
                "Transition": "fade",
                "Emotion": "informative"
            }
        ]

    return text_service.generate_scene_breakdown(
        script=script,
        duration=duration,
        visual_style=project.visual_style or "realistic",
        niche=project.niche or ""
    )


# ============================================================
# STAGE 3: CHARACTER REFERENCE
# ============================================================
def _stage_character_reference(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> Optional[Dict[str, str]]:
    """Generate character reference for visual consistency."""
    from worker.services.text import TextService

    script = results.get("generate_script", {})
    text_service = TextService()

    if not text_service.is_available():
        return None

    return text_service.generate_character_reference(
        script=script,
        niche=project.niche or "",
        visual_style=project.visual_style or "realistic"
    )


# ============================================================
# STAGE 4: VISUAL PROMPTS
# ============================================================
def _stage_visual_prompts(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> list:
    """Generate detailed visual prompts for each scene."""
    from worker.services.text import TextService

    scenes = results.get("scene_breakdown", [])
    character = results.get("character_reference")
    text_service = TextService()

    prompts = []

    for i, scene in enumerate(scenes):
        prompt_data = {
            "scene_number": scene.get("Scene Number"),
            "image_prompt": "",
            "negative_prompt": "ugly, blurry, low quality, distorted, deformed, watermark, text",
            "video_prompt": ""
        }

        if text_service.is_available():
            img = text_service.generate_image_prompt(
                scene=scene,
                visual_style=project.visual_style or "realistic",
                character_ref=character
            )
            prompt_data["image_prompt"] = img.get("positive", "")
            prompt_data["negative_prompt"] = img.get("negative", prompt_data["negative_prompt"])
            prompt_data["video_prompt"] = text_service.generate_video_prompt(
                scene=scene,
                visual_style=project.visual_style or "realistic",
                character_ref=character
            )
        else:
            prompt_data["image_prompt"] = (
                f"Scene {i+1}: {scene.get('Visual Description', '')}, "
                f"{project.visual_style or 'realistic'} style, "
                f"vertical 9:16, high quality"
            )

        prompts.append(prompt_data)

    return prompts


# ============================================================
# STAGE 5: GENERATE IMAGES
# ============================================================
def _stage_generate_images(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> list:
    """Generate images for each scene. Creates placeholder paths if AI unavailable."""
    from worker.services.image import ImageService

    scenes = results.get("scene_breakdown", [])
    prompts = results.get("visual_prompts", [])
    character = results.get("character_reference")

    image_service = ImageService()

    # Create output directory
    output_dir = os.path.join(
        settings.TEMP_DIR,
        f"job_project_{project.project_id}",
        "images"
    )
    os.makedirs(output_dir, exist_ok=True)

    if not image_service.check_model():
        logger.warning("Image generation model not available — creating placeholder paths")
        for i, scene in enumerate(scenes):
            scene["image_path"] = os.path.join(output_dir, f"scene_{i+1:02d}.png")
            scene["image_prompt_used"] = prompts[i].get("image_prompt", "") if i < len(prompts) else ""
        return scenes

    # Real image generation
    return image_service.generate_scene_images(
        scenes=scenes,
        visual_style=project.visual_style or "realistic",
        character_ref=character,
        output_dir=output_dir
    )


# ============================================================
# STAGE 6: GENERATE VOICE
# ============================================================
def _stage_generate_voice(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate voiceover audio."""
    from worker.services.voice import VoiceService

    script = results.get("generate_script", {})
    full_text = " ".join([
        str(script.get("HOOK", "")),
        str(script.get("INTRO", "")),
        str(script.get("MAIN STORY", "")),
        str(script.get("PAYOFF", "")),
        str(script.get("CTA", ""))
    ]).strip()

    voice_service = VoiceService()

    output_dir = os.path.join(
        settings.TEMP_DIR,
        f"job_project_{project.project_id}",
        "audio"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "voice.wav")

    if not voice_service.check_tts():
        logger.warning("TTS not available — returning placeholder")
        return {
            "path": "",
            "duration_seconds": project.duration or 30,
            "text": full_text,
            "model_used": "none",
            "note": "TTS not available — install kokoro or piper-tts"
        }

    return voice_service.generate_voice(
        text=full_text,
        output_path=output_path,
        voice=project.voice or "automatic",
        voice_style=project.voice_style or "automatic",
        language=project.language or "en_US",
        niche=project.niche or "",
        content_type=project.content_type or "",
        target_duration=project.duration
    )


# ============================================================
# STAGE 7: GENERATE SUBTITLES
# ============================================================
def _stage_generate_subtitles(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate SRT/VTT subtitles from voice audio."""
    from worker.services.subtitles import SubtitleService

    voice_result = results.get("generate_voice", {})
    voice_path = voice_result.get("path", "")

    subtitle_service = SubtitleService()

    output_dir = os.path.join(
        settings.TEMP_DIR,
        f"job_project_{project.project_id}",
        "subtitles"
    )
    os.makedirs(output_dir, exist_ok=True)

    if not subtitle_service.is_available() or not voice_path or not os.path.exists(voice_path):
        logger.warning("Subtitle generation not available")
        return {"srt_path": "", "vtt_path": "", "style": {}, "word_timestamps": []}

    return subtitle_service.generate_subtitles(
        audio_path=voice_path,
        output_dir=output_dir,
        language="en",
        niche=project.niche or "",
        base_filename="subtitles"
    )


# ============================================================
# STAGE 8: PREPARE MUSIC
# ============================================================
def _stage_prepare_music(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Select and prepare background music — trim to duration, add fades."""
    from worker.services.music import MusicService

    script = results.get("generate_script", {})
    full_text = " ".join(str(v) for v in script.values())

    music_service = MusicService()
    selection = music_service.select_music(
        niche=project.niche or "",
        content_type=project.content_type or "",
        script_text=full_text,
        duration=project.duration or 30
    )

    # If we have a music track, prepare it
    selected_track = selection.get("selected_track", {})
    track_path = selected_track.get("path", "")

    if track_path and os.path.exists(track_path):
        output_dir = os.path.join(
            settings.TEMP_DIR,
            f"job_project_{project.project_id}",
            "audio"
        )
        os.makedirs(output_dir, exist_ok=True)
        prepared_path = os.path.join(output_dir, "music_trimmed.wav")

        try:
            music_service.trim_music(
                audio_path=track_path,
                output_path=prepared_path,
                target_duration=project.duration or 30,
                fade_in=selection.get("fade_in_seconds", 0.5),
                fade_out=selection.get("fade_out_seconds", 1.0)
            )
            selection["prepared_path"] = prepared_path
        except Exception as e:
            logger.warning(f"Could not prepare music: {e}")

    return selection


# ============================================================
# STAGE 9: AUDIO DUCKING
# ============================================================
def _stage_audio_ducking(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Apply audio ducking — music gets quieter during speech."""
    from worker.services.music import MusicService

    voice_result = results.get("generate_voice", {})
    music_result = results.get("prepare_music", {})

    voice_path = voice_result.get("path", "")
    music_path = music_result.get("prepared_path", "")

    if not voice_path or not music_path or not os.path.exists(voice_path) or not os.path.exists(music_path):
        logger.warning("Audio ducking skipped — missing voice or music")
        return {"ducked_music_path": music_path, "skipped": True}

    output_dir = os.path.join(
        settings.TEMP_DIR,
        f"job_project_{project.project_id}",
        "audio"
    )
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "music_ducked.wav")

    music_service = MusicService()
    ducking_params = music_result.get("ducking", {})

    result_path = music_service.duck_music(
        music_path=music_path,
        voice_path=voice_path,
        output_path=output_path,
        ducking_params=ducking_params
    )

    return {"ducked_music_path": result_path, "skipped": False}


# ============================================================
# STAGE 10: SOUND EFFECTS
# ============================================================
def _stage_sfx(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze scenes and place sound effects."""
    from worker.services.sfx import SFXService

    scenes = results.get("scene_breakdown", [])
    sfx_service = SFXService()

    suggestions = sfx_service.analyze_sfx_need(
        scenes=scenes,
        niche=project.niche or "",
        content_type=project.content_type or ""
    )

    # Convert suggestions to file placements with timing
    placements = []
    timing_offset = 0.0
    output_dir = os.path.join(
        settings.TEMP_DIR,
        f"job_project_{project.project_id}",
        "sfx"
    )
    os.makedirs(output_dir, exist_ok=True)

    for scene in scenes:
        scene_duration = float(scene.get("Duration", 3))

        for sugg in suggestions:
            if sugg.get("scene_number") == scene.get("Scene Number"):
                sfx_path = sfx_service.select_sfx(sugg.get("type", ""))

                if sfx_path is None:
                    # Try procedural generation
                    proc_path = os.path.join(
                        output_dir,
                        f"{sugg.get('type')}_{scene.get('Scene Number')}.wav"
                    )
                    sfx_path = sfx_service.generate_procedural_sfx(
                        sugg.get("type", ""),
                        proc_path
                    )

                if sfx_path:
                    placements.append({
                        "path": sfx_path,
                        "timing_seconds": timing_offset + sugg.get("offset", 0.0),
                        "type": sugg.get("type", ""),
                        "volume_db": -12
                    })

        timing_offset += scene_duration

    return {"suggestions": suggestions, "placements": placements}


# ============================================================
# STAGE 11: FINAL RENDER
# ============================================================
def _stage_final_render(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Final video render using FFmpeg editor."""
    from worker.services.editor import EditorService

    editor = EditorService()

    if not editor.is_available():
        raise RuntimeError(
            "⚠️ FFmpeg is not installed. Cannot render video.\n"
            "Install FFmpeg to enable automatic editing and rendering:\n"
            "• Ubuntu/Debian: sudo apt install ffmpeg\n"
            "• macOS: brew install ffmpeg\n"
            "• Windows: Download from ffmpeg.org"
        )

    # Build timeline from scenes
    scenes = results.get("generate_images", [])
    render_dir = os.path.join(
        settings.TEMP_DIR,
        f"job_project_{project.project_id}",
        "render"
    )
    os.makedirs(render_dir, exist_ok=True)

    timeline = editor.create_timeline(scenes, render_dir)

    # Get audio paths
    voice_path = results.get("generate_voice", {}).get("path", "")
    ducking_result = results.get("audio_ducking", {})
    music_path = ducking_result.get("ducked_music_path", "")
    if not music_path:
        music_path = results.get("prepare_music", {}).get("prepared_path", "")

    # Get subtitles
    subtitle_result = results.get("generate_subtitles", {})
    subtitle_path = subtitle_result.get("srt_path", "")
    subtitle_style = subtitle_result.get("style", {})

    # Get SFX placements
    sfx_result = results.get("sfx", {})
    sfx_placements = sfx_result.get("placements", [])

    # Final output path
    final_output = os.path.join(
        settings.STORAGE_DIR,
        "projects",
        f"project_{project.project_id}",
        f"short_{project.project_id}.mp4"
    )
    os.makedirs(os.path.dirname(final_output), exist_ok=True)

    # Render!
    output_path = editor.render(
        timeline=timeline,
        voice_path=voice_path if os.path.exists(voice_path) else "",
        music_path=music_path if os.path.exists(music_path) else "",
        subtitle_path=subtitle_path if subtitle_path and os.path.exists(subtitle_path) else None,
        sfx_files=sfx_placements,
        output_path=final_output,
        subtitle_style=subtitle_style if subtitle_style else None
    )

    # Validate output
    is_valid, issues, media_info = editor.validate_output(
        output_path,
        expected_duration=project.duration
    )

    if not is_valid:
        logger.warning(f"Output validation issues: {issues}")

    # Cleanup temporary render files
    editor.cleanup_temp_files(render_dir)

    return {
        "output_path": output_path,
        "valid": is_valid,
        "validation_issues": issues,
        "media_info": media_info
    }


# ============================================================
# STAGE 12: YOUTUBE SEO
# ============================================================
def _stage_seo(project, results: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Generate YouTube SEO: titles, description, hashtags, keywords, CTA."""
    from worker.services.text import TextService

    script = results.get("generate_script", {})
    text_service = TextService()

    seo = {
        "titles": [],
        "description": "",
        "hashtags": [],
        "keywords": [],
        "cta": ""
    }

    if not text_service.is_available():
        niche = project.niche or "facts"
        seo["titles"] = [f"Amazing {niche} you need to know! #Shorts"] * 5
        seo["description"] = f"Check out this amazing content about {niche}! Don't forget to like and subscribe!"
        seo["hashtags"] = ["#shorts", "#youtubeshorts", "#viral", "#fyp", "#trending"]
        seo["keywords"] = [niche, "shorts", "viral", "trending", "amazing"]
        seo["cta"] = "Like and subscribe for more amazing content every day!"
        return seo

    try:
        seo["titles"] = text_service.generate_titles(script, project.niche or "", count=5)
    except Exception as e:
        logger.warning(f"Title generation failed: {e}")
        seo["titles"] = [f"Amazing {project.niche}! #Shorts"] * 5

    try:
        seo["description"] = text_service.generate_description(script, project.niche or "", seo["titles"])
    except Exception as e:
        logger.warning(f"Description generation failed: {e}")

    try:
        seo["hashtags"] = text_service.generate_hashtags(script, project.niche or "", count=15)
    except Exception as e:
        logger.warning(f"Hashtag generation failed: {e}")
        seo["hashtags"] = ["#shorts", "#youtubeshorts"]

    try:
        seo["keywords"] = text_service.generate_keywords(script, project.niche or "", count=10)
    except Exception as e:
        logger.warning(f"Keyword generation failed: {e}")

    try:
        seo["cta"] = text_service.generate_cta()
    except Exception as e:
        logger.warning(f"CTA generation failed: {e}")
        seo["cta"] = "Like and subscribe!"

    return seo
