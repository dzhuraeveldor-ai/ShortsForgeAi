import logging
import os
import shutil
from typing import List, Dict, Any, Optional, Tuple

from worker.utils.ffmpeg import (
    check_ffmpeg_available,
    run_ffmpeg,
    get_media_info,
    validate_output_video,
    FFmpegError
)

logger = logging.getLogger(__name__)


class EditorService:
    """
    Automatic video editing service using FFmpeg.

    Features:
    - Create timeline from scenes
    - Convert images to video with zoom/camera movement
    - Add transitions between scenes
    - Mix voice, music, SFX
    - Burn subtitles with safe zone positioning
    - Audio ducking
    - Final render to MP4 9:16
    - Output validation
    """

    # Output settings for YouTube Shorts
    DEFAULT_WIDTH = 1080
    DEFAULT_HEIGHT = 1920
    DEFAULT_FPS = 30
    DEFAULT_VIDEO_CODEC = "libx264"
    DEFAULT_AUDIO_CODEC = "aac"
    DEFAULT_BITRATE_VIDEO = "8M"
    DEFAULT_BITRATE_AUDIO = "192k"

    # Transition presets by emotion
    TRANSITION_MAP = {
        "horror": ["cut", "fade", "flash"],
        "dramatic": ["cut", "fade"],
        "energetic": ["cut", "fade", "zoom"],
        "funny": ["cut", "fade", "zoom"],
        "luxury": ["cut", "fade", "swoosh"],
        "educational": ["cut", "fade"],
        "documentary": ["cut", "fade"],
        "mysterious": ["cut", "fade"],
        "epic": ["cut", "fade", "zoom"],
        "default": ["cut", "fade"]
    }

    def __init__(self):
        self._available = None

    def is_available(self) -> bool:
        """Check if FFmpeg is available."""
        if self._available is None:
            self._available = check_ffmpeg_available()
        return self._available

    # ============================================================
    # TIMELINE
    # ============================================================
    def create_timeline(
        self,
        scenes: List[Dict[str, Any]],
        output_dir: str
    ) -> Dict[str, Any]:
        """Create editing timeline from scene data."""
        if not self.is_available():
            raise FFmpegError("FFmpeg not available for editing")

        os.makedirs(output_dir, exist_ok=True)

        timeline = {
            "scenes": [],
            "total_duration": 0.0,
            "output_dir": output_dir
        }

        for i, scene in enumerate(scenes):
            duration = float(scene.get("Duration", 3.0))
            emotion = str(scene.get("Emotion", "neutral")).lower()
            camera = str(scene.get("Camera Movement", "slow_zoom_in")).lower()

            # Select transition
            if i == 0:
                transition = "none"
            else:
                opts = None
                for key, transitions in self.TRANSITION_MAP.items():
                    if key in emotion:
                        opts = transitions
                        break
                if not opts:
                    opts = self.TRANSITION_MAP["default"]
                transition = opts[i % len(opts)]

            # Calculate zoom parameters
            zoom = self._calculate_zoom(camera, duration)

            timeline["scenes"].append({
                "index": i,
                "duration": duration,
                "start_time": timeline["total_duration"],
                "image_path": scene.get("image_path", ""),
                "video_path": scene.get("video_path", ""),
                "transition": transition,
                "camera": camera,
                "zoom": zoom,
                "scene_data": scene
            })

            timeline["total_duration"] += duration

        logger.info(
            f"Timeline created: {len(timeline['scenes'])} scenes, "
            f"total: {timeline['total_duration']:.1f}s"
        )

        return timeline

    def _calculate_zoom(self, camera: str, duration: float) -> Dict[str, Any]:
        """Calculate zoom parameters for camera movement."""
        if "zoom_in" in camera or "push" in camera:
            return {"type": "zoom_in", "z1": 1.0, "z2": min(1.3, 1.0 + duration * 0.03)}
        elif "zoom_out" in camera or "pull" in camera:
            return {"type": "zoom_out", "z1": min(1.3, 1.0 + duration * 0.03), "z2": 1.0}
        elif "pan" in camera:
            direction = "left" if "left" in camera else "right"
            return {"type": f"pan_{direction}", "amount": 0.1}
        elif "handheld" in camera:
            return {"type": "handheld", "intensity": 0.02}
        else:
            return {"type": "static", "z1": 1.0, "z2": 1.0}

    # ============================================================
    # IMAGES → VIDEO CLIPS
    # ============================================================
    def add_images(self, timeline: Dict[str, Any]) -> List[str]:
        """Convert still images to video clips with camera movement/zoom."""
        clips = []

        for i, scene in enumerate(timeline["scenes"]):
            image_path = scene.get("image_path", "")
            duration = scene["duration"]
            zoom = scene["zoom"]
            out = os.path.join(timeline["output_dir"], f"scene_{i+1:02d}.mp4")

            # If no image, create black placeholder
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Scene {i+1}: no image, creating placeholder")
                ok, _ = run_ffmpeg(
                    ["-f", "lavfi", "-i",
                     f"color=c=black:s={self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}:d={duration}:r={self.DEFAULT_FPS}",
                     "-c:v", self.DEFAULT_VIDEO_CODEC, "-preset", "fast",
                     "-pix_fmt", "yuv420p", "-an", out],
                    f"placeholder scene {i+1}"
                )
                if ok:
                    clips.append(out)
                    scene["clip_path"] = out
                continue

            # Build zoom filter
            zf = self._build_zoom_filter(zoom, duration)

            args = [
                "-loop", "1",
                "-i", image_path,
                "-t", str(duration),
                "-vf", (
                    f"scale={self.DEFAULT_WIDTH}:{self.DEFAULT_HEIGHT}:"
                    f"force_original_aspect_ratio=decrease,"
                    f"pad={self.DEFAULT_WIDTH}:{self.DEFAULT_HEIGHT}:"
                    f"(ow-iw)/2:(oh-ih)/2:color=black,"
                    f"{zf},"
                    f"setsar=1,fps={self.DEFAULT_FPS}"
                ),
                "-c:v", self.DEFAULT_VIDEO_CODEC,
                "-preset", "fast",
                "-pix_fmt", "yuv420p",
                "-an",
                out
            ]

            ok, error = run_ffmpeg(args, f"scene {i+1} image→video")

            if ok and os.path.exists(out):
                clips.append(out)
                scene["clip_path"] = out
            else:
                logger.error(f"Scene {i+1} failed: {error}")
                # Fallback: simple scale without zoom
                run_ffmpeg(
                    ["-loop", "1", "-i", image_path, "-t", str(duration),
                     "-vf", f"scale={self.DEFAULT_WIDTH}:{self.DEFAULT_HEIGHT},setsar=1,fps={self.DEFAULT_FPS}",
                     "-c:v", self.DEFAULT_VIDEO_CODEC, "-preset", "fast",
                     "-pix_fmt", "yuv420p", "-an", out],
                    f"scene {i+1} fallback"
                )
                clips.append(out)
                scene["clip_path"] = out

        return clips

    def _build_zoom_filter(self, zoom: Dict[str, Any], duration: float) -> str:
        """Build FFmpeg zoompan filter string."""
        ztype = zoom.get("type", "static")
        fps = self.DEFAULT_FPS

        if ztype == "zoom_in":
            z1, z2 = zoom["z1"], zoom["z2"]
            return (
                f"zoompan=z='{z1}+({z2}-{z1})*on/(duration*{fps})':"
                f"d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s={self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}:fps={fps}"
            )
        elif ztype == "zoom_out":
            z1, z2 = zoom["z1"], zoom["z2"]
            return (
                f"zoompan=z='{z1}+({z2}-{z1})*on/(duration*{fps})':"
                f"d=1:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                f"s={self.DEFAULT_WIDTH}x{self.DEFAULT_HEIGHT}:fps={fps}"
            )
        elif ztype == "handheld":
            intensity = zoom.get("intensity", 0.02) * 100
            return (
                f"scale={self.DEFAULT_WIDTH + 20}:{self.DEFAULT_HEIGHT + 20},"
                f"crop={self.DEFAULT_WIDTH}:{self.DEFAULT_HEIGHT}:"
                f"'({self.DEFAULT_WIDTH + 20}-{self.DEFAULT_WIDTH})/2+{intensity}*sin(2*PI*t*3)':"
                f"'({self.DEFAULT_HEIGHT + 20}-{self.DEFAULT_HEIGHT})/2+{intensity}*cos(2*PI*t*2.5)'"
            )
        else:
            return f"scale={self.DEFAULT_WIDTH}:{self.DEFAULT_HEIGHT}"

    # ============================================================
    # CONCATENATE CLIPS
    # ============================================================
    def concat_clips(self, clips: List[str], output_path: str) -> str:
        """Concatenate video clips using concat demuxer."""
        if len(clips) == 1:
            shutil.copy2(clips[0], output_path)
            return output_path

        concat_file = os.path.join(os.path.dirname(output_path), "concat_list.txt")
        with open(concat_file, "w") as f:
            for clip in clips:
                f.write(f"file '{os.path.abspath(clip)}'\n")

        ok, error = run_ffmpeg(
            ["-f", "concat", "-safe", "0", "-i", concat_file, "-c", "copy", output_path],
            "concatenate clips"
        )

        if not ok:
            logger.warning(f"Stream copy concat failed ({error}), re-encoding")
            # Build inputs for xfade
            inputs = []
            for c in clips:
                inputs.extend(["-i", c])

            # Simple crossfade between first pair
            if len(clips) == 2:
                try:
                    info0 = get_media_info(clips[0])
                    dur0 = info0["duration"]
                    td = 0.3
                    filter_c = (
                        f"[0:v][1:v]xfade=transition=fade:duration={td}:offset={dur0 - td}[v];"
                    )
                    run_ffmpeg(
                        inputs + [
                            "-filter_complex", filter_c,
                            "-map", "[v]",
                            "-c:v", self.DEFAULT_VIDEO_CODEC, "-preset", "fast",
                            "-pix_fmt", "yuv420p", output_path
                        ],
                        "xfade concat"
                    )
                except Exception:
                    raise FFmpegError("Could not concatenate clips")

        return output_path

    # ============================================================
    # AUDIO MIXING
    # ============================================================
    def add_voice(self, video_path: str, voice_path: str, output_path: str) -> str:
        """Add voiceover to video."""
        if not voice_path or not os.path.exists(voice_path):
            shutil.copy2(video_path, output_path)
            return output_path

        ok, error = run_ffmpeg(
            ["-i", video_path, "-i", voice_path,
             "-c:v", "copy", "-c:a", self.DEFAULT_AUDIO_CODEC,
             "-b:a", self.DEFAULT_BITRATE_AUDIO, "-shortest", output_path],
            "add voiceover"
        )

        if not ok:
            raise FFmpegError(f"Failed to add voice: {error}")

        return output_path

    def add_music(
        self,
        video_path: str,
        music_path: str,
        output_path: str,
        music_volume_db: float = -20.0
    ) -> str:
        """Mix background music into video."""
        if not music_path or not os.path.exists(music_path):
            shutil.copy2(video_path, output_path)
            return output_path

        vol = 10 ** (music_volume_db / 20)

        ok, error = run_ffmpeg(
            ["-i", video_path, "-i", music_path,
             "-filter_complex",
             f"[1:a]volume={vol}[music];"
             f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[aout]",
             "-map", "0:v", "-map", "[aout]",
             "-c:v", "copy", "-c:a", self.DEFAULT_AUDIO_CODEC,
             "-b:a", self.DEFAULT_BITRATE_AUDIO, "-shortest", output_path],
            "mix music"
        )

        if not ok:
            logger.warning(f"Music mix failed: {error}")
            shutil.copy2(video_path, output_path)

        return output_path

    def apply_audio_ducking(
        self,
        video_path: str,
        voice_path: str,
        music_path: str,
        output_path: str
    ) -> str:
        """Apply sidechain compression — music ducks when voice is active."""
        if not voice_path or not music_path or not os.path.exists(voice_path) or not os.path.exists(music_path):
            return self.add_music(video_path, music_path, output_path, music_volume_db=-24)

        ok, error = run_ffmpeg(
            ["-i", video_path, "-i", voice_path, "-i", music_path,
             "-filter_complex",
             "[1:a][2:a]sidechaincompress="
             "threshold=-35:ratio=4:attack=0.05:release=0.2[ducked];"
             "[1:a][ducked]amix=inputs=2:duration=first[aout]",
             "-map", "0:v", "-map", "[aout]",
             "-c:v", "copy", "-c:a", self.DEFAULT_AUDIO_CODEC,
             "-b:a", self.DEFAULT_BITRATE_AUDIO, "-shortest", output_path],
            "audio ducking"
        )

        if not ok:
            logger.warning(f"Ducking failed: {error}")
            return self.add_music(video_path, music_path, output_path, music_volume_db=-24)

        return output_path

    def add_sfx(
        self,
        video_path: str,
        sfx_files: List[Dict[str, Any]],
        output_path: str
    ) -> str:
        """Mix sound effects at specific timing points."""
        if not sfx_files:
            shutil.copy2(video_path, output_path)
            return output_path

        # Build complex filter for multiple SFX
        inputs = ["-i", video_path]
        filter_parts = []
        last_audio = "0:a"
        valid_sfx = []

        for sfx in sfx_files:
            path = sfx.get("path", "")
            if not path or not os.path.exists(path):
                continue
            valid_sfx.append(sfx)

        if not valid_sfx:
            shutil.copy2(video_path, output_path)
            return output_path

        for i, sfx in enumerate(valid_sfx):
            path = sfx["path"]
            timing = sfx.get("timing_seconds", 0.0)
            vol_db = sfx.get("volume_db", -12)
            vol = 10 ** (vol_db / 20)

            inputs.extend(["-i", path])
            idx = i + 1
            delay_ms = int(timing * 1000)
            sfx_label = f"sfx{i}"
            mixed_label = f"mix{i}"

            filter_parts.append(
                f"[{idx}:a]adelay={delay_ms}|{delay_ms},volume={vol}[{sfx_label}]"
            )

            if i == 0:
                filter_parts.append(f"[0:a][{sfx_label}]amix=inputs=2:duration=first[{mixed_label}]")
            else:
                filter_parts.append(f"[{last_audio}][{sfx_label}]amix=inputs=2:duration=first[{mixed_label}]")

            last_audio = mixed_label

        filter_complex = ";".join(filter_parts)

        ok, error = run_ffmpeg(
            inputs + [
                "-filter_complex", filter_complex,
                "-map", "0:v", "-map", f"[{last_audio}]",
                "-c:v", "copy", "-c:a", self.DEFAULT_AUDIO_CODEC,
                "-b:a", self.DEFAULT_BITRATE_AUDIO, "-shortest", output_path
            ],
            "mix SFX"
        )

        if not ok:
            logger.warning(f"SFX mix failed: {error}")
            shutil.copy2(video_path, output_path)

        return output_path

    # ============================================================
    # SUBTITLES
    # ============================================================
    def add_subtitles(
        self,
        video_path: str,
        subtitle_path: str,
        output_path: str,
        style: Optional[Dict[str, Any]] = None
    ) -> str:
        """Burn subtitles into video with Shorts safe zone positioning."""
        if not subtitle_path or not os.path.exists(subtitle_path):
            shutil.copy2(video_path, output_path)
            return output_path

        if style is None:
            style = {}

        font = style.get("font", "Arial")
        font_size = style.get("font_size", 28)
        color_hex = style.get("color", "#FFFFFF")
        outline_hex = style.get("outline_color", "#000000")
        outline_width = style.get("outline_width", 3)

        # Convert hex → ASS color format (&HAABBGGRR)
        def hex_to_ass(h):
            h = h.lstrip("#")
            r, g, b = h[0:2], h[2:4], h[4:6]
            return f"&H00{b}{g}{r}"

        primary = hex_to_ass(color_hex)
        outline = hex_to_ass(outline_hex)

        # Safe zone: 12% margin from bottom for Shorts
        margin_v = int(self.DEFAULT_HEIGHT * 0.12)

        style_str = (
            f"FontName={font},FontSize={font_size},"
            f"PrimaryColour={primary},OutlineColour={outline},"
            f"BackColour=&H80000000,Bold=1,Italic=0,"
            f"BorderStyle=1,Outline={outline_width},Shadow=0,"
            f"Alignment=2,MarginL=40,MarginR=40,MarginV={margin_v},Encoding=0"
        )

        # Escape path for FFmpeg filter
        escaped = subtitle_path.replace("\\", "/").replace(":", "\\:")

        ok, error = run_ffmpeg(
            ["-i", video_path,
             "-vf", f"subtitles='{escaped}':force_style='{style_str}'",
             "-c:v", self.DEFAULT_VIDEO_CODEC, "-preset", "fast",
             "-pix_fmt", "yuv420p", "-c:a", "copy", output_path],
            "burn subtitles"
        )

        if not ok:
            raise FFmpegError(f"Failed to burn subtitles: {error}")

        return output_path

    # ============================================================
    # FINAL RENDER
    # ============================================================
    def render(
        self,
        timeline: Dict[str, Any],
        voice_path: str,
        music_path: str,
        subtitle_path: Optional[str] = None,
        sfx_files: Optional[List[Dict[str, Any]]] = None,
        output_path: str = "output.mp4",
        subtitle_style: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Full automatic render pipeline:
        1. Images → video clips
        2. Concatenate
        3. Add voice
        4. Audio ducking / music
        5. Add SFX
        6. Burn subtitles
        7. Final encode with faststart
        """
        if not self.is_available():
            raise FFmpegError(
                "⚠️ FFmpeg not installed. Install FFmpeg to enable editing:\n"
                "• Ubuntu: sudo apt install ffmpeg\n"
                "• macOS: brew install ffmpeg"
            )

        output_dir = timeline["output_dir"]
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        stage = 0

        def log(name):
            nonlocal stage
            stage += 1
            logger.info(f"Render stage {stage}/7: {name}")

        try:
            # Stage 1: Images → clips
            log("Images → video clips")
            clips = self.add_images(timeline)

            # Stage 2: Concatenate
            log("Concatenate clips")
            s1 = os.path.join(output_dir, "01_video_only.mp4")
            self.concat_clips(clips, s1)

            # Stage 3: Add voice
            log("Add voiceover")
            s2 = os.path.join(output_dir, "02_with_voice.mp4")
            if voice_path and os.path.exists(voice_path):
                self.add_voice(s1, voice_path, s2)
            else:
                shutil.copy2(s1, s2)

            # Stage 4: Music + audio ducking
            log("Music & audio ducking")
            s3 = os.path.join(output_dir, "03_with_music.mp4")
            if music_path and os.path.exists(music_path) and voice_path and os.path.exists(voice_path):
                self.apply_audio_ducking(s2, voice_path, music_path, s3)
            elif music_path and os.path.exists(music_path):
                self.add_music(s2, music_path, s3)
            else:
                shutil.copy2(s2, s3)

            # Stage 5: SFX
            log("Add sound effects")
            s4 = os.path.join(output_dir, "04_with_sfx.mp4")
            self.add_sfx(s3, sfx_files or [], s4)

            # Stage 6: Subtitles
            log("Burn subtitles")
            s5 = os.path.join(output_dir, "05_with_subs.mp4")
            if subtitle_path and os.path.exists(subtitle_path):
                self.add_subtitles(s4, subtitle_path, s5, subtitle_style)
            else:
                shutil.copy2(s4, s5)

            # Stage 7: Final encode with faststart for YouTube
            log("Final encode (faststart)")
            ok, error = run_ffmpeg(
                ["-i", s5,
                 "-c:v", self.DEFAULT_VIDEO_CODEC, "-preset", "medium",
                 "-crf", "23", "-pix_fmt", "yuv420p",
                 "-movflags", "+faststart",
                 "-c:a", self.DEFAULT_AUDIO_CODEC,
                 "-b:a", self.DEFAULT_BITRATE_AUDIO, "-ar", "44100",
                 output_path],
                "final render",
                timeout=600
            )

            if not ok:
                raise FFmpegError(f"Final render failed: {error}")

            logger.info(f"✅ Final render complete: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Render pipeline failed: {e}")
            raise

    # ============================================================
    # VALIDATION & CLEANUP
    # ============================================================
    def validate_output(
        self,
        output_path: str,
        expected_duration: Optional[float] = None
    ) -> Tuple[bool, List[str], Dict[str, Any]]:
        """Validate final output video file."""
        try:
            info = get_media_info(output_path)
        except Exception as e:
            return False, [str(e)], {}

        valid, issues = validate_output_video(
            output_path,
            expected_duration=expected_duration,
            expected_aspect_ratio="9:16",
            min_width=720,
            require_audio=True
        )

        return valid, issues, info

    def cleanup_temp_files(self, directory: str) -> int:
        """Clean up intermediate render files."""
        removed = 0
        if not os.path.exists(directory):
            return 0

        for filename in os.listdir(directory):
            filepath = os.path.join(directory, filename)
            if filename.endswith((".mp4", ".wav", ".srt", ".vtt", ".txt")):
                try:
                    os.remove(filepath)
                    removed += 1
                except Exception as e:
                    logger.debug(f"Could not remove {filepath}: {e}")

        logger.info(f"Cleaned up {removed} temp files from {directory}")
        return removed
