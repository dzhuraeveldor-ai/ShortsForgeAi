import logging
import asyncio
import json
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from worker.config import settings
from worker.models.model_manager import model_manager
from worker.utils.hardware import get_hardware_info
from database.database import get_db_session
from database.repositories import (
    GenerationJobRepository,
    ProjectRepository,
    WorkerStatusRepository,
    ModelStatusRepository
)

logger = logging.getLogger(__name__)


# ============================================================
# PYDANTIC SCHEMAS
# ============================================================
class JobCreate(BaseModel):
    user_id: int
    project_id: Optional[int] = None
    job_type: str = Field(..., description="Job type: full_short, image, video, voice, subtitles")
    parameters: dict = Field(default_factory=dict)


class JobResponse(BaseModel):
    job_id: int
    user_id: int
    project_id: Optional[int]
    type: str
    status: str
    created_at: Optional[str]
    started_at: Optional[str]
    completed_at: Optional[str]
    progress: Optional[dict]
    error: Optional[str]


class HealthResponse(BaseModel):
    status: str
    worker: str
    version: str
    hardware: dict
    capabilities: dict
    models: dict
    queue: dict


# ============================================================
# LIFESPAN — STARTUP & SHUTDOWN
# ============================================================
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    logger.info("=" * 60)
    logger.info("ShortsForge AI Worker API starting...")
    logger.info(f"Version: {settings.APP_VERSION}")
    logger.info(f"Worker ID: {settings.WORKER_ID}")

    # Update worker status to ONLINE
    db = await anext(get_db_session())
    worker_repo = WorkerStatusRepository(db)
    hw_info = get_hardware_info()
    capabilities = model_manager.get_capabilities()

    await worker_repo.update_worker_status(
        worker_id=settings.WORKER_ID,
        status="online",
        hardware_info=hw_info,
        capabilities=capabilities
    )

    # Update model statuses in database
    model_repo = ModelStatusRepository(db)
    model_statuses = model_manager.get_model_statuses()

    for category, models in model_statuses.items():
        for model in models:
            await model_repo.update_model_status(
                category=category,
                model_name=model["name"],
                available=model.get("available", False),
                details=model
            )

    await db.close()

    # Start background job processor
    asyncio.create_task(job_processor())

    logger.info("Worker API ready and accepting requests")
    logger.info("=" * 60)

    yield

    # Shutdown
    logger.info("Worker shutting down...")
    db = await anext(get_db_session())
    await WorkerStatusRepository(db).update_worker_status(
        worker_id=settings.WORKER_ID,
        status="offline"
    )
    await db.close()
    logger.info("Worker stopped")


# ============================================================
# CREATE FASTAPI APP
# ============================================================
app = FastAPI(
    title="ShortsForge AI Worker API",
    description="API for AI Worker that handles text/image/video/voice generation and automatic video editing",
    version=settings.APP_VERSION,
    lifespan=lifespan
)


# ============================================================
# BACKGROUND JOB PROCESSOR
# ============================================================
async def job_processor():
    """Background task that continuously processes jobs from the queue."""
    from worker.jobs.processor import process_job

    logger.info("Background job processor started")
    consecutive_errors = 0

    while True:
        try:
            db = await anext(get_db_session())
            job_repo = GenerationJobRepository(db)

            # Get next queued job
            job = await job_repo.get_next_queued_job()

            if job:
                logger.info(
                    f"Processing job #{job.job_id} | "
                    f"type: {job.type} | user: {job.user_id}"
                )

                # Mark as processing
                await job_repo.update_status(job.job_id, "processing")

                # Run in thread pool (AI tasks are CPU/GPU intensive)
                loop = asyncio.get_event_loop()
                try:
                    await loop.run_in_executor(
                        None,
                        process_job,
                        job.job_id,
                        job.type,
                        job.parameters or {}
                    )

                    await job_repo.update_status(job.job_id, "completed")
                    consecutive_errors = 0
                    logger.info(f"Job #{job.job_id} completed successfully")

                except Exception as e:
                    error_msg = str(e)[:500]
                    logger.error(f"Job #{job.job_id} FAILED: {error_msg}")
                    await job_repo.update_status(
                        job.job_id,
                        "failed",
                        error=error_msg
                    )
                    consecutive_errors += 1

            await db.close()

            # Sleep between checks
            if job:
                await asyncio.sleep(1)
            else:
                await asyncio.sleep(5)

            # Prevent infinite error loop
            if consecutive_errors > 10:
                logger.error("Too many consecutive errors — pausing processor for 60 seconds")
                await asyncio.sleep(60)
                consecutive_errors = 0

        except Exception as e:
            logger.error(f"Job processor error: {e}")
            await asyncio.sleep(10)


# ============================================================
# HEALTH ENDPOINT
# ============================================================
@app.get("/health", response_model=HealthResponse, summary="Worker health status")
async def health_check():
    """Get worker health status, hardware info, capabilities and queue stats."""
    db = await anext(get_db_session())
    try:
        job_repo = GenerationJobRepository(db)

        queue_stats = {
            "queued": await job_repo.count_by_status("queued"),
            "processing": await job_repo.count_by_status("processing"),
            "completed": await job_repo.count_by_status("completed"),
            "failed": await job_repo.count_by_status("failed"),
            "cancelled": await job_repo.count_by_status("cancelled")
        }

        return HealthResponse(
            status="healthy",
            worker=settings.WORKER_ID,
            version=settings.APP_VERSION,
            hardware=get_hardware_info(),
            capabilities=model_manager.get_capabilities(),
            models=model_manager.get_model_statuses(),
            queue=queue_stats
        )
    finally:
        await db.close()


# ============================================================
# JOBS ENDPOINTS
# ============================================================
@app.post("/jobs", response_model=JobResponse, status_code=201, summary="Create new job")
async def create_job(data: JobCreate):
    """Create a new generation job and add it to the queue."""
    db = await anext(get_db_session())
    try:
        job_repo = GenerationJobRepository(db)
        project_repo = ProjectRepository(db)

        # Validate project ownership if provided
        if data.project_id:
            project = await project_repo.get_by_id(data.project_id)
            if not project or project.user_id != data.user_id:
                raise HTTPException(status_code=403, detail="Project not found or access denied")

        # Check queue size limit
        queued_count = await job_repo.count_by_status("queued")
        if queued_count >= settings.MAX_QUEUE_SIZE:
            raise HTTPException(
                status_code=503,
                detail=f"Queue is full. Maximum {settings.MAX_QUEUE_SIZE} jobs allowed."
            )

        # Create job
        job = await job_repo.create(
            user_id=data.user_id,
            project_id=data.project_id,
            type=data.job_type,
            status="queued",
            parameters=data.parameters,
            progress={"current_stage": 0, "stages": []}
        )

        # Update project status
        if data.project_id:
            await project_repo.update_status(data.project_id, "queued")

        return JobResponse(
            job_id=job.job_id,
            user_id=job.user_id,
            project_id=job.project_id,
            type=job.type,
            status=job.status,
            created_at=job.created_at.isoformat() if job.created_at else None,
            started_at=None,
            completed_at=None,
            progress=job.progress,
            error=None
        )
    finally:
        await db.close()


@app.get("/jobs/{job_id}", response_model=JobResponse, summary="Get job status")
async def get_job(job_id: int):
    """Get job details and current status."""
    db = await anext(get_db_session())
    try:
        job = await GenerationJobRepository(db).get_by_id(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return JobResponse(
            job_id=job.job_id,
            user_id=job.user_id,
            project_id=job.project_id,
            type=job.type,
            status=job.status,
            created_at=job.created_at.isoformat() if job.created_at else None,
            started_at=job.started_at.isoformat() if job.started_at else None,
            completed_at=job.completed_at.isoformat() if job.completed_at else None,
            progress=job.progress,
            error=job.error
        )
    finally:
        await db.close()


@app.post("/jobs/{job_id}/cancel", summary="Cancel job")
async def cancel_job(job_id: int):
    """Cancel a queued or processing job."""
    db = await anext(get_db_session())
    try:
        repo = GenerationJobRepository(db)
        job = await repo.get_by_id(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status in ["completed", "failed", "cancelled"]:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot cancel job with status: {job.status}"
            )

        await repo.update_status(job_id, "cancelled")
        return {"status": "cancelled", "job_id": job_id}
    finally:
        await db.close()


@app.post("/jobs/{job_id}/retry", summary="Retry failed job")
async def retry_job(job_id: int):
    """Retry a failed job — resets it to queued status."""
    db = await anext(get_db_session())
    try:
        repo = GenerationJobRepository(db)
        job = await repo.get_by_id(job_id)

        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        if job.status != "failed":
            raise HTTPException(status_code=400, detail="Only failed jobs can be retried")

        await repo.update_status(
            job_id,
            "queued",
            error=None,
            started_at=None,
            completed_at=None,
            progress={"current_stage": 0, "retry": True}
        )

        return {"status": "retried", "job_id": job_id, "new_status": "queued"}
    finally:
        await db.close()


# ============================================================
# MODELS & CAPABILITIES
# ============================================================
@app.get("/models", summary="Get available AI models")
async def get_models():
    """Get list of all AI models and their availability status."""
    return {"models": model_manager.get_model_statuses()}


@app.get("/capabilities", summary="Get worker capabilities")
async def get_capabilities():
    """Get what this worker can do (text, image, video, voice, etc.) and hardware info."""
    return {
        "capabilities": model_manager.get_capabilities(),
        "hardware": get_hardware_info()
    }


# ============================================================
# ERROR HANDLERS
# ============================================================
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled API error: {exc}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error"}
    )
