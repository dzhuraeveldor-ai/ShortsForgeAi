import httpx
import logging
from typing import Optional, Dict, Any

from config import bot_settings

logger = logging.getLogger(__name__)


class WorkerClient:
    """HTTP client for communicating with AI Worker API."""

    def __init__(self, base_url: str = None, timeout: int = None):
        self.base_url = base_url or bot_settings.WORKER_API_URL
        self.timeout = timeout or bot_settings.WORKER_TIMEOUT

    async def _request(self, method: str, path: str, **kwargs) -> Any:
        """Make HTTP request to Worker."""
        url = f"{self.base_url}{path}"

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Worker HTTP error {e.response.status_code}: {e.response.text[:200]}")
            raise RuntimeError(f"Worker error: {e.response.status_code}")
        except httpx.ConnectError:
            logger.error(f"Worker connection refused: {self.base_url}")
            raise RuntimeError(
                "⚠️ AI Worker офлайн.\n"
                "Запусти Worker командой: python -m worker.main"
            )
        except Exception as e:
            logger.error(f"Worker request failed: {e}")
            raise RuntimeError(f"Worker connection error: {str(e)[:100]}")

    async def is_healthy(self) -> bool:
        """Check if Worker is online and healthy."""
        try:
            await self._request("GET", "/health")
            return True
        except Exception:
            return False

    async def get_health(self) -> Dict[str, Any]:
        """Get full health status."""
        return await self._request("GET", "/health")

    async def create_job(
        self,
        user_id: int,
        project_id: Optional[int],
        job_type: str,
        parameters: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create new generation job."""
        data = {
            "user_id": user_id,
            "project_id": project_id,
            "job_type": job_type,
            "parameters": parameters or {}
        }
        return await self._request("POST", "/jobs", json=data)

    async def get_job(self, job_id: int) -> Dict[str, Any]:
        """Get job status."""
        return await self._request("GET", f"/jobs/{job_id}")

    async def cancel_job(self, job_id: int) -> Dict[str, Any]:
        """Cancel job."""
        return await self._request("POST", f"/jobs/{job_id}/cancel")

    async def retry_job(self, job_id: int) -> Dict[str, Any]:
        """Retry failed job."""
        return await self._request("POST", f"/jobs/{job_id}/retry")

    async def get_models(self) -> Dict[str, Any]:
        """Get available AI models."""
        return await self._request("GET", "/models")

    async def get_capabilities(self) -> Dict[str, Any]:
        """Get worker capabilities."""
        return await self._request("GET", "/capabilities")
