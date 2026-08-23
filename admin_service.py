from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from bot.services.user_service import UserService
from bot.services.project_service import ProjectService
from database.repositories import GenerationJobRepository


class AdminService:
    """Service for admin operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_service = UserService(db)
        self.project_service = ProjectService(db)
        self.job_repo = GenerationJobRepository(db)

    async def get_statistics(self) -> Dict[str, Any]:
        """Get system-wide statistics."""
        total_users = await self.user_service.count_all()
        total_projects = await self.project_service.count_all()

        total_jobs = 0
        completed_jobs = 0
        queued_jobs = 0
        processing_jobs = 0
        failed_jobs = 0

        try:
            from sqlalchemy import select, func
            from database.models import GenerationJob

            result = await self.db.execute(select(func.count(GenerationJob.job_id)))
            total_jobs = result.scalar() or 0

            completed_jobs = await self.job_repo.count_by_status("completed")
            queued_jobs = await self.job_repo.count_by_status("queued")
            processing_jobs = await self.job_repo.count_by_status("processing")
            failed_jobs = await self.job_repo.count_by_status("failed")
        except Exception:
            pass

        return {
            "total_users": total_users,
            "total_projects": total_projects,
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "queued_jobs": queued_jobs,
            "processing_jobs": processing_jobs,
            "failed_jobs": failed_jobs
        }

    async def get_queue(self, limit: int = 20) -> List[Any]:
        """Get current queue of jobs."""
        from sqlalchemy import select
        from database.models import GenerationJob

        result = await self.db.execute(
            select(GenerationJob)
            .where(GenerationJob.status.in_(["queued", "processing"]))
            .order_by(GenerationJob.created_at.asc())
            .limit(limit)
        )
        return list(result.scalars().all())
