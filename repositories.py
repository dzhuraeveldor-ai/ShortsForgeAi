"""
Database repositories for AI Shorts Studio.
Provides clean data access layer for all entities.
"""

from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import select, update, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User, Limit, Project, GenerationJob, AdminAction, Settings


# ============================================
# User Repository
# ============================================

class UserRepository:
    """Data access for User entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(self, user_id: int, username: Optional[str] = None,
                            first_name: Optional[str] = None, is_admin: bool = False) -> User:
        """Get existing user or create new one."""
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                user_id=user_id,
                username=username,
                first_name=first_name,
                is_admin=is_admin,
            )
            self.db.add(user)
            await self.db.flush()
        else:
            # Update last active and info
            user.last_active = datetime.utcnow()
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            await self.db.flush()

        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        result = await self.db.execute(select(User).where(User.user_id == user_id))
        return result.scalar_one_or_none()

    async def get_all(self, offset: int = 0, limit: int = 50) -> List[User]:
        """Get all users with pagination."""
        result = await self.db.execute(
            select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count_all(self) -> int:
        """Count total users."""
        result = await self.db.execute(select(func.count(User.user_id)))
        return result.scalar_one()

    async def count_active(self, hours: int = 24) -> int:
        """Count active users in last N hours."""
        since = datetime.utcnow() - timedelta(hours=hours)
        result = await self.db.execute(
            select(func.count(User.user_id)).where(User.last_active >= since)
        )
        return result.scalar_one()

    async def set_blocked(self, user_id: int, blocked: bool) -> Optional[User]:
        """Block or unblock user."""
        user = await self.get_by_id(user_id)
        if user:
            user.blocked = blocked
            await self.db.flush()
        return user

    async def set_unlimited(self, user_id: int, unlimited: bool) -> Optional[User]:
        """Set unlimited access for user."""
        user = await self.get_by_id(user_id)
        if user:
            user.unlimited = unlimited
            await self.db.flush()
        return user


# ============================================
# Limit Repository
# ============================================

class LimitRepository:
    """Data access for usage limits with rolling 24h window."""

    # Default free limits
    DEFAULT_LIMITS = {
        "ideas": 10,
        "scripts": 5,
        "hooks": 10,
        "images": 5,
        "videos": 1,
        "voice": 3,
        "subtitles": 3,
        "full_shorts": 1,
        "analysis": 3,
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_or_create(self, user_id: int, limit_type: str) -> Limit:
        """Get or create limit record."""
        result = await self.db.execute(
            select(Limit).where(and_(Limit.user_id == user_id, Limit.limit_type == limit_type))
        )
        limit = result.scalar_one_or_none()

        if limit is None:
            limit = Limit(user_id=user_id, limit_type=limit_type, count=0, last_reset=datetime.utcnow())
            self.db.add(limit)
            await self.db.flush()

        return limit

    async def _check_reset(self, limit: Limit) -> Limit:
        """Reset counter if 24h window passed."""
        if datetime.utcnow() - limit.last_reset >= timedelta(hours=24):
            limit.count = 0
            limit.last_reset = datetime.utcnow()
            await self.db.flush()
        return limit

    async def can_use(self, user_id: int, limit_type: str, is_admin_or_unlimited: bool = False) -> bool:
        """Check if user can perform action."""
        if is_admin_or_unlimited:
            return True

        max_limit = self.DEFAULT_LIMITS.get(limit_type, 1)
        limit = await self._get_or_create(user_id, limit_type)
        limit = await self._check_reset(limit)
        return limit.count < max_limit

    async def increment(self, user_id: int, limit_type: str, is_admin_or_unlimited: bool = False) -> None:
        """Increment usage counter."""
        if is_admin_or_unlimited:
            return

        limit = await self._get_or_create(user_id, limit_type)
        limit = await self._check_reset(limit)
        limit.count += 1
        await self.db.flush()

    async def get_remaining(self, user_id: int, limit_type: str, is_admin_or_unlimited: bool = False) -> int:
        """Get remaining uses."""
        if is_admin_or_unlimited:
            return 999

        max_limit = self.DEFAULT_LIMITS.get(limit_type, 1)
        limit = await self._get_or_create(user_id, limit_type)
        limit = await self._check_reset(limit)
        return max(0, max_limit - limit.count)

    async def reset(self, user_id: int, limit_type: Optional[str] = None) -> None:
        """Reset limits for user."""
        if limit_type:
            limit = await self._get_or_create(user_id, limit_type)
            limit.count = 0
            limit.last_reset = datetime.utcnow()
        else:
            for lt in self.DEFAULT_LIMITS.keys():
                limit = await self._get_or_create(user_id, lt)
                limit.count = 0
                limit.last_reset = datetime.utcnow()
        await self.db.flush()

    async def get_all(self, user_id: int) -> dict:
        """Get all limits for user."""
        result = {}
        for limit_type in self.DEFAULT_LIMITS.keys():
            limit = await self._get_or_create(user_id, limit_type)
            limit = await self._check_reset(limit)
            max_limit = self.DEFAULT_LIMITS[limit_type]
            result[limit_type] = {
                "used": limit.count,
                "max": max_limit,
                "remaining": max(0, max_limit - limit.count),
            }
        return result


# ============================================
# Project Repository
# ============================================

class ProjectRepository:
    """Data access for Project entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: int, **kwargs) -> Project:
        """Create new project."""
        project = Project(user_id=user_id, **kwargs)
        self.db.add(project)
        await self.db.flush()
        return project

    async def get_by_id(self, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def get_by_user(self, user_id: int, offset: int = 0, limit: int = 20) -> List[Project]:
        """Get user's projects."""
        result = await self.db.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_user(self, user_id: int) -> int:
        """Count user's projects."""
        result = await self.db.execute(
            select(func.count(Project.id)).where(Project.user_id == user_id)
        )
        return result.scalar_one()

    async def update(self, project_id: int, **kwargs) -> Optional[Project]:
        """Update project fields."""
        project = await self.get_by_id(project_id)
        if project:
            for key, value in kwargs.items():
                setattr(project, key, value)
            project.updated_at = datetime.utcnow()
            await self.db.flush()
        return project

    async def delete(self, project_id: int) -> bool:
        """Delete project."""
        result = await self.db.execute(delete(Project).where(Project.id == project_id))
        await self.db.flush()
        return result.rowcount > 0

    async def count_all(self) -> int:
        """Count total projects."""
        result = await self.db.execute(select(func.count(Project.id)))
        return result.scalar_one()

    async def count_by_status(self, status: str) -> int:
        """Count projects by status."""
        result = await self.db.execute(
            select(func.count(Project.id)).where(Project.status == status)
        )
        return result.scalar_one()


# ============================================
# Generation Job Repository
# ============================================

class JobRepository:
    """Data access for GenerationJob entities."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, project_id: int, job_type: str, payload: Optional[dict] = None) -> GenerationJob:
        """Create new generation job."""
        job = GenerationJob(project_id=project_id, job_type=job_type, payload=payload)
        self.db.add(job)
        await self.db.flush()
        return job

    async def get_by_id(self, job_id: int) -> Optional[GenerationJob]:
        """Get job by ID."""
        result = await self.db.execute(select(GenerationJob).where(GenerationJob.id == job_id))
        return result.scalar_one_or_none()

    async def get_next_queued(self) -> Optional[GenerationJob]:
        """Get next queued job for processing."""
        result = await self.db.execute(
            select(GenerationJob)
            .where(GenerationJob.status == "queued")
            .order_by(GenerationJob.created_at.asc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update(self, job_id: int, **kwargs) -> Optional[GenerationJob]:
        """Update job fields."""
        job = await self.get_by_id(job_id)
        if job:
            for key, value in kwargs.items():
                setattr(job, key, value)
            await self.db.flush()
        return job

    async def get_queue_stats(self) -> dict:
        """Get queue statistics."""
        stats = {}
        for status in ["queued", "processing", "completed", "failed", "waiting_for_worker", "cancelled"]:
            result = await self.db.execute(
                select(func.count(GenerationJob.id)).where(GenerationJob.status == status)
            )
            stats[status] = result.scalar_one()
        return stats

    async def count_all(self) -> int:
        """Count total jobs."""
        result = await self.db.execute(select(func.count(GenerationJob.id)))
        return result.scalar_one()


# ============================================
# Admin Action Repository
# ============================================

class AdminActionRepository:
    """Data access for admin action logging."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def log(self, admin_id: int, action: str, target_user_id: Optional[int] = None,
                  details: Optional[dict] = None) -> AdminAction:
        """Log an admin action."""
        entry = AdminAction(
            admin_id=admin_id,
            action=action,
            target_user_id=target_user_id,
            details=details,
        )
        self.db.add(entry)
        await self.db.flush()
        return entry


# ============================================
# Settings Repository
# ============================================

class SettingsRepository:
    """Data access for global settings."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get setting value."""
        result = await self.db.execute(select(Settings).where(Settings.key == key))
        setting = result.scalar_one_or_none()
        return setting.value if setting else default

    async def set(self, key: str, value: str) -> None:
        """Set setting value."""
        result = await self.db.execute(select(Settings).where(Settings.key == key))
        setting = result.scalar_one_or_none()

        if setting:
            setting.value = value
        else:
            setting = Settings(key=key, value=value)
            self.db.add(setting)
        await self.db.flush()
