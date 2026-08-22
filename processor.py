import logging
import os
import json
from datetime import datetime
from typing import Dict, Any

from worker.config import settings
from database.database import get_db_session_sync
from database.repositories import (
    GenerationJobRepository,
    ProjectRepository,
    UsageEventRepository
)

logger = logging.getLogger(__name__)


def _make_serializable(obj: Any) -> Any:
    """Make any object JSON-serializable for database storage."""
    if isinstance(obj, dict):
        return {k: _make_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_make_serializable(item) for item in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, '__dict__'):
        return str(obj)
    else:
        try:
            json.dumps(obj)
            return obj
        except (TypeError, ValueError):
            return str(obj)


def _record_usage(db, user_id: int, job_type: str) -> None:
    """Record usage event for limit tracking after successful job completion."""
    try:
        operation_map = {
            "full_short": "shorts",
            "image": "images",
            "video": "videos",
            "voice": "voice",
            "subtitles": "subtitles"
        }
        operation = operation_map.get(job_type)
        if operation:
            UsageEventRepository(db).add_event_sync(user_id, operation)
            logger.info(f"Usage recorded: user={user_id}, operation={operation}")
    except Exception as e:
        logger.warning(f"Could not record usage: {e}")


def process_job(job_id: int, job_type: str, parameters: Dict[str, Any]):
    """
    Main job processing function.
    Runs in a separate thread from the async event loop.

    Features:
    - Resume from last completed stage
    - Progress tracking
    - Error handling per stage
    - Usage recording on success
    """
    logger.info(f"=" * 50)
    logger.info(f"Starting job #{job_id} | type: {job_type}")
    logger.info(f"=" * 50)

    # Get synchronous DB session (runs in thread)
    db = get_db_session_sync()

    try:
        job_repo = GenerationJobRepository(db)
        project_repo = ProjectRepository(db)

        # Load job
        job = job_repo.get_by_id_sync(job_id)
        if not job:
            raise ValueError(f"Job #{job_id} not found in database")

        # Load project if applicable
        project = None
        if job.project_id:
            project = project_repo.get_by_id_sync(job.project_id)
            if not project:
                logger.warning(f"Job #{job_id}: project #{job.project_id} not found")

        # Get progress and completed stages (for resume)
        progress = job.progress or {}
        completed_stages = progress.get("completed_stages", {})
        stage_results = progress.get("stage_results", {})

        # Build pipeline based on job type
        if job_type == "full_short":
            from worker.jobs.stages import create_stages
            pipeline = create_stages(project, parameters)
        else:
            raise ValueError(f"Unsupported job type: {job_type}")

        total_stages = len(pipeline)
        logger.info(f"Pipeline: {total_stages} stages")

        # Update project status
        if project:
            project_repo.update_status_sync(project.project_id, "processing")

        # Execute each stage
        for idx, stage in enumerate(pipeline, 1):
            stage_name = stage.name
            display_name = stage.display_name

            # Skip if already completed (RESUME feature)
            if stage_name in completed_stages:
                logger.info(f"Stage {idx}/{total_stages}: {display_name} — ALREADY COMPLETED, skipping")
                continue

            logger.info(f"Stage {idx}/{total_stages}: {display_name}")

            # Update progress in DB
            progress.update({
                "current_stage": idx,
                "total_stages": total_stages,
                "current_stage_name": display_name
            })
            job_repo.update_sync(job_id, progress=progress)

            try:
                # Execute the stage function
                result = stage.function(stage_results)

                # Store result
                stage_results[stage_name] = result
                completed_stages[stage_name] = {
                    "completed_at": datetime.utcnow().isoformat()
                }

                # Save progress
                progress["completed_stages"] = completed_stages
                progress["stage_results"] = _make_serializable(stage_results)
                job_repo.update_sync(job_id, progress=progress)

                # Also update project for UI
                if project:
                    project_repo.update_completed_stages_sync(
                        project.project_id,
                        completed_stages
                    )

                logger.info(f"Stage {idx}/{total_stages}: {display_name} — ✅ COMPLETED")

            except Exception as e:
                error_message = f"Stage '{display_name}' failed: {str(e)[:300]}"
                logger.error(f"Job #{job_id}: {error_message}")

                progress["failed_stage"] = stage_name
                progress["failed_stage_display"] = display_name
                job_repo.update_sync(
                    job_id,
                    progress=progress,
                    error=error_message[:500]
                )

                if project:
                    project_repo.update_status_sync(project.project_id, "failed")

                raise RuntimeError(error_message)

        # ALL STAGES COMPLETED
        final_output = stage_results.get("final_render", {})

        progress["current_stage"] = total_stages
        progress["completed_at"] = datetime.utcnow().isoformat()
        progress["final_output"] = _make_serializable(final_output)

        job_repo.update_sync(
            job_id,
            progress=progress,
            status="completed",
            result_data=_make_serializable(final_output)
        )

        # Update project with output path
        if project:
            output_path = final_output.get("output_path", "")
            seo_data = stage_results.get("seo", {})
            project_repo.update_sync(
                project.project_id,
                status="ready",
                output_path=output_path,
                seo_data=_make_serializable(seo_data)
            )

        logger.info(f"=" * 50)
        logger.info(f"Job #{job_id} — 🎉 ALL STAGES COMPLETED")
        logger.info(f"=" * 50)

        # Record usage for limits
        _record_usage(db, job.user_id, job_type)

        return final_output

    except Exception as e:
        logger.error(f"Job #{job_id} FAILED: {e}")
        raise
    finally:
        db.close()
