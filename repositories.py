from sqlalchemy import select, update, delete, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from .models import (
    Project, GenerationJob, WorkerStatus, ModelStatus,
    UsageEvent, UserSettings, AdminAction
)
from .database import SyncSessionLocal


# ============================================================
# PROJECT REPOSITORY
# ============================================================
class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> Project:
        project = Project(**kwargs)
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def get_by_id(self, project_id: int) -> Optional[Project]:
        return await self.db.get(Project, project_id)

    async def get_by_user(self, user_id: int, limit: int = 50) -> List[Project]:
        result = await self.db.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(self, project_id: int, status: str):
        await self.db.execute(
            update(Project)
            .where(Project.project_id == project_id)
            .values(status=status, updated_at=datetime.utcnow())
        )
        await self.db.commit()

    async def update_completed_stages(self, project_id: int, stages: dict):
        await self.db.execute(
            update(Project)
            .where(Project.project_id == project_id)
            .values(completed_stages=stages, updated_at=datetime.utcnow())
        )
        await self.db.commit()

    async def update(self, project_id: int, **kwargs):
        kwargs["updated_at"] = datetime.utcnow()
        await self.db.execute(
            update(Project)
            .where(Project.project_id == project_id)
            .values(**kwargs)
        )
        await self.db.commit()

    async def delete(self, project_id: int) -> bool:
        result = await self.db.execute(
            delete(Project).where(Project.project_id == project_id)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def count_by_user(self, user_id: int) -> int:
        result = await self.db.execute(
            select(func.count(Project.project_id)).where(Project.user_id == user_id)
        )
        return result.scalar() or 0

    # Sync versions for job processor threads
    def get_by_id_sync(self, project_id: int) -> Optional[Project]:
        with SyncSessionLocal() as db:
            return db.get(Project, project_id)

    def update_status_sync(self, project_id: int, status: str):
        with SyncSessionLocal() as db:
            db.execute(
                update(Project)
                .where(Project.project_id == project_id)
                .values(status=status, updated_at=datetime.utcnow())
            )
            db.commit()

    def update_sync(self, project_id: int, **kwargs):
        with SyncSessionLocal() as db:
            if "updated_at" not in kwargs:
                kwargs["updated_at"] = datetime.utcnow()
            db.execute(
                update(Project)
                .where(Project.project_id == project_id)
                .values(**kwargs)
            )
            db.commit()

    def update_completed_stages_sync(self, project_id: int, stages: dict):
        with SyncSessionLocal() as db:
            db.execute(
                update(Project)
                .where(Project.project_id == project_id)
                .values(completed_stages=stages, updated_at=datetime.utcnow())
            )
            db.commit()


# ============================================================
# GENERATION JOB REPOSITORY
# ============================================================
class GenerationJobRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, **kwargs) -> GenerationJob:
        job = GenerationJob(**kwargs)
        self.db.add(job)
        await self.db.commit()
        await self.db.refresh(job)
        return job

    async def get_by_id(self, job_id: int) -> Optional[GenerationJob]:
        return await self.db.get(GenerationJob, job_id)

    async def get_by_user(self, user_id: int, limit: int = 20) -> List[GenerationJob]:
        result = await self.db.execute(
            select(GenerationJob)
            .where(GenerationJob.user_id == user_id)
            .order_by(GenerationJob.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_next_queued_job(self) -> Optional[GenerationJob]:
        result = await self.db.execute(
            select(GenerationJob)
            .where(GenerationJob.status == "queued")
            .order_by(
                GenerationJob.priority.desc(),
                GenerationJob.created_at.asc()
            )
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_status(
        self,
        job_id: int,
        status: str,
        error: str = None,
        **kwargs
    ):
        values = {"status": status}
        if status == "processing":
            values["started_at"] = datetime.utcnow()
        if status in ["completed", "failed", "cancelled"]:
            values["completed_at"] = datetime.utcnow()
        if error:
            values["error"] = error
        values.update(kwargs)

        await self.db.execute(
            update(GenerationJob)
            .where(GenerationJob.job_id == job_id)
            .values(**values)
        )
        await self.db.commit()

    async def count_by_status(self, status: str) -> int:
        result = await self.db.execute(
            select(func.count(GenerationJob.job_id))
            .where(GenerationJob.status == status)
        )
        return result.scalar() or 0

    async def count_by_user_and_status(self, user_id: int, status: str) -> int:
        result = await self.db.execute(
            select(func.count(GenerationJob.job_id))
            .where(
                GenerationJob.user_id == user_id,
                GenerationJob.status == status
            )
        )
        return result.scalar() or 0

    # Sync versions
    def get_by_id_sync(self, job_id: int) -> Optional[GenerationJob]:
        with SyncSessionLocal() as db:
            return db.get(GenerationJob, job_id)

    def update_sync(self, job_id: int, **kwargs) -> bool:
        with SyncSessionLocal() as db:
            result = db.execute(
                update(GenerationJob)
                .where(GenerationJob.job_id == job_id)
                .values(**kwargs)
            )
            db.commit()
            return result.rowcount > 0


# ============================================================
# WORKER STATUS REPOSITORY
# ============================================================
class WorkerStatusRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_worker_status(
        self,
        worker_id: str,
        status: str,
        hardware_info: dict = None,
        capabilities: dict = None
    ):
        # Try to update existing
        result = await self.db.execute(
            update(WorkerStatus)
            .where(WorkerStatus.worker_id == worker_id)
            .values(
                status=status,
                last_seen=datetime.utcnow(),
                hardware_info=hardware_info,
                capabilities=capabilities
            )
        )

        if result.rowcount == 0:
            # Create new
            worker = WorkerStatus(
                worker_id=worker_id,
                status=status,
                hardware_info=hardware_info,
                capabilities=capabilities
            )
            self.db.add(worker)

        await self.db.commit()

    async def get_all(self) -> List[WorkerStatus]:
        result = await self.db.execute(select(WorkerStatus))
        return list(result.scalars().all())


# ============================================================
# MODEL STATUS REPOSITORY
# ============================================================
class ModelStatusRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def update_model_status(
        self,
        category: str,
        model_name: str,
        available: bool,
        details: dict
    ):
        # Try update
        result = await self.db.execute(
            update(ModelStatus)
            .where(
                ModelStatus.category == category,
                ModelStatus.model_name == model_name
            )
            .values(
                available=available,
                details=details,
                updated_at=datetime.utcnow()
            )
        )

        if result.rowcount == 0:
            rec = ModelStatus(
                category=category,
                model_name=model_name,
                available=available,
                details=details
            )
            self.db.add(rec)

        await self.db.commit()

    async def get_all(self) -> List[ModelStatus]:
        result = await self.db.execute(select(ModelStatus))
        return list(result.scalars().all())


# ============================================================
# USAGE EVENT REPOSITORY (для лимитов)
# ============================================================
class UsageEventRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_event(self, user_id: int, operation_type: str):
        event = UsageEvent(user_id=user_id, operation_type=operation_type)
        self.db.add(event)
        await self.db.commit()

    async def count_events_24h(self, user_id: int, operation_type: str) -> int:
        since = datetime.utcnow() - timedelta(hours=24)
        result = await self.db.execute(
            select(func.count(UsageEvent.id))
            .where(
                UsageEvent.user_id == user_id,
                UsageEvent.operation_type == operation_type,
                UsageEvent.created_at >= since
            )
        )
        return result.scalar() or 0

    # Sync version
    def add_event_sync(self, user_id: int, operation_type: str):
        with SyncSessionLocal() as db:
            db.add(UsageEvent(user_id=user_id, operation_type=operation_type))
            db.commit()


# ============================================================
# USER SETTINGS REPOSITORY
# ============================================================
class UserSettingsRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: int) -> UserSettings:
        result = await self.db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()

        if not settings:
            settings = UserSettings(user_id=user_id)
            self.db.add(settings)
            await self.db.commit()
            await self.db.refresh(settings)

        return settings

    async def update(self, user_id: int, **kwargs):
        kwargs["updated_at"] = datetime.utcnow()
        await self.db.execute(
            update(UserSettings)
            .where(UserSettings.user_id == user_id)
            .values(**kwargs)
        )
        await self.db.commit()


# ============================================================
# ADMIN ACTION REPOSITORY
# ============================================================
class AdminActionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def log_action(
        self,
        admin_id: int,
        action: str,
        target_user_id: int = None,
        details: dict = None
    ):
        log = AdminAction(
            admin_id=admin_id,
            action=action,
            target_user_id=target_user_id,
            details=details
        )
        self.db.add(log)
        await self.db.commit()

    async def get_recent(self, limit: int = 50) -> List[AdminAction]:
        result = await self.db.execute(
            select(AdminAction)
            .order_by(AdminAction.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
