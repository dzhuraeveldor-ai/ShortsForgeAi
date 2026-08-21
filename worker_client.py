"""
Worker API client for Bot Server.
Handles communication with AI Worker via HTTP.
"""

from typing import Optional, Any
import httpx
from loguru import logger

from bot.config import config


class WorkerClient:
    """Client for communicating with AI Worker API."""

    def __init__(self, base_url: str = config.WORKER_URL, api_key: str = config.WORKER_API_KEY):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self._headers = {"X-API-Key": self.api_key, "Content-Type": "application/json"}

    async def health_check(self) -> dict:
        """Check worker health status."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.warning(f"Worker health check failed: {e}")
            return {"status": "offline", "error": str(e)}

    async def is_online(self) -> bool:
        """Quick check if worker is online."""
        health = await self.health_check()
        return health.get("status") == "online"

    async def submit_job(self, job_type: str, payload: dict) -> dict:
        """Submit a new job to worker."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.base_url}/jobs",
                    headers=self._headers,
                    json={"job_type": job_type, "payload": payload},
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to submit job: {e}")
            return {"status": "error", "error": str(e)}

    async def get_job(self, job_id: str) -> dict:
        """Get job status and result."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.base_url}/jobs/{job_id}",
                    headers=self._headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to get job {job_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def cancel_job(self, job_id: str) -> dict:
        """Cancel a running job."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/jobs/{job_id}/cancel",
                    headers=self._headers,
                )
                response.raise_for_status()
                return response.json()
        except Exception as e:
            logger.error(f"Failed to cancel job {job_id}: {e}")
            return {"status": "error", "error": str(e)}

    async def generate_text(self, prompt: str, system_prompt: Optional[str] = None,
                          max_tokens: int = 2048, temperature: float = 0.7) -> dict:
        """Generate text via worker."""
        return await self.submit_job("text", {
            "prompt": prompt,
            "system_prompt": system_prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        })

    async def generate_hooks(self, niche: str, content_type: str, language: str = "american_english",
                           count: int = 5) -> dict:
        """Generate hooks for a short."""
        return await self.submit_job("hooks", {
            "niche": niche,
            "content_type": content_type,
            "language": language,
            "count": count,
        })

    async def generate_ideas(self, niche: str, content_type: str, hook: Optional[str] = None,
                           language: str = "american_english", count: int = 5) -> dict:
        """Generate video ideas."""
        return await self.submit_job("ideas", {
            "niche": niche,
            "content_type": content_type,
            "hook": hook,
            "language": language,
            "count": count,
        })

    async def generate_script(self, niche: str, content_type: str, idea: str, hook: str,
                            duration: int, language: str = "american_english",
                            voice_style: str = "auto") -> dict:
        """Generate full script."""
        return await self.submit_job("script", {
            "niche": niche,
            "content_type": content_type,
            "idea": idea,
            "hook": hook,
            "duration": duration,
            "language": language,
            "voice_style": voice_style,
        })

    async def generate_scenes(self, script: str, duration: int, visual_style: str,
                            niche: str) -> dict:
        """Break script into scenes."""
        return await self.submit_job("scenes", {
            "script": script,
            "duration": duration,
            "visual_style": visual_style,
            "niche": niche,
        })

    async def generate_image(self, prompt: str, negative_prompt: Optional[str] = None,
                           width: int = 576, height: int = 1024,
                           num_inference_steps: int = 30) -> dict:
        """Generate a single image."""
        return await self.submit_job("image", {
            "prompt": prompt,
            "negative_prompt": negative_prompt,
            "width": width,
            "height": height,
            "num_inference_steps": num_inference_steps,
        })

    async def generate_voice(self, text: str, gender: str = "auto", style: str = "auto",
                           language: str = "american_english", speed: float = 1.0) -> dict:
        """Generate voice audio."""
        return await self.submit_job("voice", {
            "text": text,
            "gender": gender,
            "style": style,
            "language": language,
            "speed": speed,
        })

    async def generate_subtitles(self, audio_path: str, language: str = "auto") -> dict:
        """Generate subtitles from audio."""
        return await self.submit_job("subtitles", {
            "audio_path": audio_path,
            "language": language,
        })

    async def render_video(self, project_data: dict) -> dict:
        """Request full video rendering."""
        return await self.submit_job("render", project_data)

    async def analyze_video(self, video_path: str) -> dict:
        """Analyze an existing video."""
        return await self.submit_job("analyze", {
            "video_path": video_path,
        })

    async def generate_seo(self, script: str, niche: str, content_type: str,
                         language: str = "american_english") -> dict:
        """Generate YouTube SEO metadata."""
        return await self.submit_job("seo", {
            "script": script,
            "niche": niche,
            "content_type": content_type,
            "language": language,
        })


# Global worker client instance
worker_client = WorkerClient()
