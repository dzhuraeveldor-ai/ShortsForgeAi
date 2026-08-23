import logging
import os
import subprocess
import shutil
import json
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class FFmpegError(Exception):
    """Custom exception for FFmpeg errors."""
    pass


def check_ffmpeg_available() -> bool:
    """Check if FFmpeg and FFprobe are installed."""
    return bool(shutil.which("ffmpeg")) and bool(shutil.which("ffprobe"))


def get_ffmpeg_version() -> Optional[str]:
    """Get FFmpeg version string."""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            first_line = result.stdout.split("\n")[0]
            parts = first_line.split("version")
            if len(parts) > 1:
                return parts[1].split()[0].strip()
    except Exception as e:
        logger.warning(f"Could not get FFmpeg version: {e}")
    return None


def run_ffmpeg(
    args: List[str],
    description: str = "FFmpeg operation",
    timeout: int = 600
) -> Tuple[bool, str]:
    """
    Run FFmpeg command SAFELY (never shell=True).
    Returns (success: bool, error_message: str).
    """
    if not check_ffmpeg_available():
        raise FFmpegError(
            "⚠️ FFmpeg is not installed.\n"
            "Install FFmpeg first:\n"
            "  • Ubuntu/Debian: sudo apt install ffmpeg\n"
            "  • macOS: brew install ffmpeg\n"
            "  • Windows: Download from ffmpeg.org"
        )

    full_cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"] + args

    logger.debug(f"FFmpeg ({description}): {' '.join(full_cmd)}")

    try:
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            shell=False  # CRITICAL SECURITY: never use shell=True
        )

        if result.returncode != 0:
            error = result.stderr.strip() or f"Exit code {result.returncode}"
            logger.error(f"FFmpeg FAILED ({description}): {error[:300]}")
            return False, error

        logger.info(f"FFmpeg OK ({description})")
        return True, ""

    except subprocess.TimeoutExpired:
        msg = f"FFmpeg timed out after {timeout}s ({description})"
        logger.error(msg)
        return False, msg
    except Exception as e:
        msg = f"FFmpeg error ({description}): {str(e)}"
        logger.error(msg)
        return False, msg


def get_media_info(file_path: str) -> Dict[str, Any]:
    """
    Get media file info using ffprobe.
    Returns dict with: duration, width, height, codec, has_audio, file_size.
    """
    if not os.path.exists(file_path):
        raise FFmpegError(f"File not found: {file_path}")

    if not check_ffmpeg_available():
        raise FFmpegError("FFmpeg not installed")

    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-print_format", "json",
                "-show_format", "-show_streams",
                file_path
            ],
            capture_output=True, text=True, timeout=30, shell=False
        )

        if result.returncode != 0:
            raise FFmpegError(f"ffprobe failed: {result.stderr[:200]}")

        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        streams = data.get("streams", [])

        video = next((s for s in streams if s.get("codec_type") == "video"), None)
        audio = next((s for s in streams if s.get("codec_type") == "audio"), None)

        return {
            "duration": float(fmt.get("duration", 0)),
            "width": int(video.get("width", 0)) if video else 0,
            "height": int(video.get("height", 0)) if video else 0,
            "codec": video.get("codec_name", "") if video else "",
            "has_audio": audio is not None,
            "audio_codec": audio.get("codec_name", "") if audio else "",
            "file_size": int(fmt.get("size", 0)),
            "bit_rate": int(fmt.get("bit_rate", 0)) if fmt.get("bit_rate") else 0
        }

    except json.JSONDecodeError as e:
        raise FFmpegError(f"Invalid ffprobe output: {e}")
    except FFmpegError:
        raise
    except Exception as e:
        raise FFmpegError(f"Failed to probe media: {str(e)}")


def validate_output_video(
    file_path: str,
    expected_duration: Optional[float] = None,
    expected_aspect_ratio: str = "9:16",
    min_width: int = 720,
    require_audio: bool = True
) -> Tuple[bool, List[str]]:
    """
    Validate output video file.
    Checks: existence, size, duration, aspect ratio, resolution, audio, codec.
    """
    issues = []

    if not os.path.exists(file_path):
        issues.append("File does not exist")
        return False, issues

    if os.path.getsize(file_path) < 1024:
        issues.append(f"File too small: {os.path.getsize(file_path)} bytes")
        return False, issues

    try:
        info = get_media_info(file_path)
    except FFmpegError as e:
        issues.append(str(e))
        return False, issues

    # Duration check
    if expected_duration is not None:
        actual = info["duration"]
        tolerance = max(1.0, expected_duration * 0.1)
        if abs(actual - expected_duration) > tolerance:
            issues.append(
                f"Duration mismatch: expected {expected_duration:.1f}s, got {actual:.1f}s"
            )

    # Aspect ratio check (9:16 for Shorts)
    if info["width"] > 0 and info["height"] > 0:
        expected = expected_aspect_ratio.split(":")
        exp_w, exp_h = int(expected[0]), int(expected[1])
        actual_ratio = info["width"] / info["height"]
        expected_ratio = exp_w / exp_h
        if abs(actual_ratio - expected_ratio) > 0.05:
            issues.append(
                f"Wrong aspect ratio: {info['width']}x{info['height']} "
                f"(expected {expected_aspect_ratio})"
            )

    # Minimum resolution
    if info["width"] < min_width:
        issues.append(f"Width too low: {info['width']} < {min_width}")

    # Audio check
    if require_audio and not info["has_audio"]:
        issues.append("No audio track found")

    # Codec compatibility
    if info["codec"] and info["codec"] not in ["h264", "vp9", "av1"]:
        issues.append(f"Non-standard codec: {info['codec']}")

    return len(issues) == 0, issues
