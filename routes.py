"""
Worker API routes for AI Shorts Studio.
FastAPI endpoints for job management and health checks.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Header, Request
from fastapi.responses import JSONResponse
from loguru import logger

from worker.config import config
from worker.models import JobRequest, JobResponse, HealthResponse, JobStatus, JobType
from worker.services.model_manager import model_manager
from worker.services.text import text_service
from worker.services.image import image_service
from worker.services.video import video_service
from worker.services.voice import voice_service
from worker.services.stt import stt_service
from worker.services.music import music_service
from worker.services.editor import editor_service


router = APIRouter()

# In-memory job store (for standalone worker)
_jobs: dict[str, dict] = {}


# ============================================
# API Key Authentication
# ============================================

async def verify_api_key(x_api_key: Optional[str] = Header(None)) -> None:
    """Verify API key for protected endpoints."""
    if x_api_key != config.API_KEY:
        raise HTTPException(status_code=401, detail="Invalid API key")


# ============================================
# Health Check
# ============================================

@router.get("/health", response_model=HealthResponse, summary="Worker health status")
async def health_check() -> HealthResponse:
    """Check worker health, GPU info, and available models."""
    return HealthResponse(
        status="online",
        gpu=model_manager.gpu_info,
        vram=model_manager.vram_info,
        models=model_manager.models,
    )


# ============================================
# Job Management
# ============================================

@router.post("/jobs", response_model=JobResponse, summary="Submit a new job")
async def submit_job(
    request: JobRequest,
    api_key_ok: None = Depends(verify_api_key),
) -> JobResponse:
    """Submit a new AI job for processing."""
    job_id = str(uuid.uuid4())

    job = {
        "job_id": job_id,
        "job_type": request.job_type,
        "status": JobStatus.QUEUED,
        "progress": 0,
        "payload": request.payload,
        "result": None,
        "error": None,
        "created_at": datetime.utcnow(),
        "started_at": None,
        "completed_at": None,
    }

    _jobs[job_id] = job

    # Start processing in background
    asyncio.create_task(_process_job(job_id))

    return _job_to_response(job)


@router.get("/jobs/{job_id}", response_model=JobResponse, summary="Get job status and result")
async def get_job(
    job_id: str,
    api_key_ok: None = Depends(verify_api_key),
) -> JobResponse:
    """Get job status, progress, and result."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return _job_to_response(job)


@router.post("/jobs/{job_id}/cancel", response_model=JobResponse, summary="Cancel a running job")
async def cancel_job(
    job_id: str,
    api_key_ok: None = Depends(verify_api_key),
) -> JobResponse:
    """Cancel a queued or processing job."""
    job = _jobs.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job["status"] in [JobStatus.QUEUED, JobStatus.PROCESSING]:
        job["status"] = JobStatus.CANCELLED
        job["completed_at"] = datetime.utcnow()

    return _job_to_response(job)


# ============================================
# Direct Service Endpoints (convenience)
# ============================================

@router.post("/generate/text", summary="Direct text generation")
async def direct_generate_text(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct text generation endpoint."""
    result = await text_service.generate_text(
        prompt=request.get("prompt", ""),
        system_prompt=request.get("system_prompt"),
        max_tokens=request.get("max_tokens", 2048),
        temperature=request.get("temperature", 0.7),
    )
    return {"status": "success", "result": result}


@router.post("/generate/hooks", summary="Direct hooks generation")
async def direct_generate_hooks(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct hooks generation endpoint."""
    result = await text_service.generate_hooks(
        niche=request.get("niche", "general"),
        content_type=request.get("content_type", "story"),
        language=request.get("language", "american_english"),
        count=request.get("count", 5),
    )
    return {"status": "success", "result": result}


@router.post("/generate/ideas", summary="Direct ideas generation")
async def direct_generate_ideas(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct ideas generation endpoint."""
    result = await text_service.generate_ideas(
        niche=request.get("niche", "general"),
        content_type=request.get("content_type", "story"),
        hook=request.get("hook"),
        language=request.get("language", "american_english"),
        count=request.get("count", 5),
    )
    return {"status": "success", "result": result}


@router.post("/generate/script", summary="Direct script generation")
async def direct_generate_script(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct script generation endpoint."""
    result = await text_service.generate_script(
        niche=request.get("niche", "general"),
        content_type=request.get("content_type", "story"),
        idea=request.get("idea", ""),
        hook=request.get("hook", ""),
        duration=request.get("duration", 30),
        language=request.get("language", "american_english"),
        voice_style=request.get("voice_style", "auto"),
    )
    return {"status": "success", "result": result}


@router.post("/generate/scenes", summary="Direct scene breakdown")
async def direct_generate_scenes(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct scene breakdown endpoint."""
    result = await text_service.generate_scenes(
        script=request.get("script", ""),
        duration=request.get("duration", 30),
        visual_style=request.get("visual_style", "cinematic"),
        niche=request.get("niche", "general"),
    )
    return {"status": "success", "result": result}


@router.post("/generate/image", summary="Direct image generation")
async def direct_generate_image(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct image generation endpoint."""
    result = await image_service.generate_image(
        prompt=request.get("prompt", ""),
        negative_prompt=request.get("negative_prompt"),
        width=request.get("width", config.IMAGE_DEFAULT_WIDTH),
        height=request.get("height", config.IMAGE_DEFAULT_HEIGHT),
        num_inference_steps=request.get("num_inference_steps", config.IMAGE_DEFAULT_STEPS),
    )
    return {"status": "success", "result": result}


@router.post("/generate/voice", summary="Direct voice generation")
async def direct_generate_voice(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct voice generation endpoint."""
    result = await voice_service.generate_voice(
        text=request.get("text", ""),
        gender=request.get("gender", "auto"),
        style=request.get("style", "auto"),
        language=request.get("language", "american_english"),
        speed=request.get("speed", 1.0),
    )
    return {"status": "success", "result": result}


@router.post("/generate/subtitles", summary="Direct subtitle generation")
async def direct_generate_subtitles(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct subtitle generation from audio."""
    result = await stt_service.generate_subtitles(
        audio_path=request.get("audio_path", ""),
        language=request.get("language", "auto"),
    )
    return {"status": "success", "result": result}


@router.post("/generate/seo", summary="Direct SEO metadata generation")
async def direct_generate_seo(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Direct YouTube SEO generation endpoint."""
    result = await text_service.generate_seo(
        script=request.get("script", ""),
        niche=request.get("niche", "general"),
        content_type=request.get("content_type", "story"),
        language=request.get("language", "american_english"),
    )
    return {"status": "success", "result": result}


@router.post("/render", summary="Full video render")
async def direct_render(
    request: dict,
    api_key_ok: None = Depends(verify_api_key),
) -> dict:
    """Full automatic video rendering endpoint."""
    result = await editor_service.render_short(request)
    return result


# ============================================
# Job Processing
# ============================================

async def _process_job(job_id: str) -> None:
    """Process a job in background."""
    job = _jobs.get(job_id)
    if not job:
        return

    try:
        job["status"] = JobStatus.PROCESSING
        job["started_at"] = datetime.utcnow()
        job["progress"] = 5

        job_type = job["job_type"]
        payload = job["payload"] or {}

        logger.info(f"⚙️ Processing job {job_id} type={job_type}")

        result = None

        if job_type == JobType.TEXT:
            result = await text_service.generate_text(
                prompt=payload.get("prompt", ""),
                system_prompt=payload.get("system_prompt"),
                max_tokens=payload.get("max_tokens", 2048),
                temperature=payload.get("temperature", 0.7),
            )

        elif job_type == JobType.HOOKS:
            result = await text_service.generate_hooks(
                niche=payload.get("niche", "general"),
                content_type=payload.get("content_type", "story"),
                language=payload.get("language", "american_english"),
                count=payload.get("count", 5),
            )

        elif job_type == JobType.IDEAS:
            result = await text_service.generate_ideas(
                niche=payload.get("niche", "general"),
                content_type=payload.get("content_type", "story"),
                hook=payload.get("hook"),
                language=payload.get("language", "american_english"),
                count=payload.get("count", 5),
            )

        elif job_type == JobType.SCRIPT:
            result = await text_service.generate_script(
                niche=payload.get("niche", "general"),
                content_type=payload.get("content_type", "story"),
                idea=payload.get("idea", ""),
                hook=payload.get("hook", ""),
                duration=payload.get("duration", 30),
                language=payload.get("language", "american_english"),
                voice_style=payload.get("voice_style", "auto"),
            )

        elif job_type == JobType.SCENES:
            result = await text_service.generate_scenes(
                script=payload.get("script", ""),
                duration=payload.get("duration", 30),
                visual_style=payload.get("visual_style", "cinematic"),
                niche=payload.get("niche", "general"),
            )

        elif job_type == JobType.IMAGE:
            job["progress"] = 30
            result = await image_service.generate_image(
                prompt=payload.get("prompt", ""),
                negative_prompt=payload.get("negative_prompt"),
                width=payload.get("width", config.IMAGE_DEFAULT_WIDTH),
                height=payload.get("height", config.IMAGE_DEFAULT_HEIGHT),
                num_inference_steps=payload.get("num_inference_steps", config.IMAGE_DEFAULT_STEPS),
            )

        elif job_type == JobType.VIDEO:
            job["progress"] = 30
            if payload.get("image_path"):
                result = await video_service.image_to_video(
                    image_path=payload["image_path"],
                    prompt=payload.get("prompt"),
                    duration=payload.get("duration", 3),
                )
            else:
                result = await video_service.text_to_video(
                    prompt=payload.get("prompt", ""),
                    duration=payload.get("duration", 5),
                )

        elif job_type == JobType.VOICE:
            result = await voice_service.generate_voice(
                text=payload.get("text", ""),
                gender=payload.get("gender", "auto"),
                style=payload.get("style", "auto"),
                language=payload.get("language", "american_english"),
                speed=payload.get("speed", 1.0),
            )

        elif job_type == JobType.SUBTITLES:
            result = await stt_service.generate_subtitles(
                audio_path=payload.get("audio_path", ""),
                language=payload.get("language", "auto"),
            )

        elif job_type == JobType.SEO:
            result = await text_service.generate_seo(
                script=payload.get("script", ""),
                niche=payload.get("niche", "general"),
                content_type=payload.get("content_type", "story"),
                language=payload.get("language", "american_english"),
            )

        elif job_type == JobType.RENDER:
            job["progress"] = 10
            result = await editor_service.render_short(payload)
            if result.get("status") == "error":
                raise RuntimeError(result.get("error", "Render failed"))

        elif job_type == JobType.ANALYZE:
            result = {
                "analysis": {
                    "hook": 7,
                    "pacing": 7,
                    "visuals": 7,
                    "audio": 7,
                    "ending": 7,
                    "overall": 7,
                    "suggestions": [
                        "Make hook more impactful",
                        "Improve pacing in middle section",
                        "Add stronger CTA at end",
                    ],
                }
            }

        else:
            raise ValueError(f"Unknown job type: {job_type}")

        job["result"] = result
        job["status"] = JobStatus.COMPLETED
        job["progress"] = 100
        job["completed_at"] = datetime.utcnow()

        logger.info(f"✅ Job {job_id} completed")

    except Exception as e:
        logger.error(f"❌ Job {job_id} failed: {e}")
        job["status"] = JobStatus.FAILED
        job["error"] = str(e)
        job["completed_at"] = datetime.utcnow()


def _job_to_response(job: dict) -> JobResponse:
    """Convert internal job dict to API response model."""
    return JobResponse(
        job_id=job["job_id"],
        job_type=job["job_type"],
        status=job["status"],
        progress=job.get("progress", 0),
        result=job.get("result"),
        error=job.get("error"),
        created_at=job["created_at"],
        started_at=job.get("started_at"),
        completed_at=job.get("completed_at"),
    )
