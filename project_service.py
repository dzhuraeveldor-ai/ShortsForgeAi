from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict, Any

from database.repositories import ProjectRepository


class ProjectService:
    """Service for managing projects."""

    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)

    async def create(self, **kwargs) -> Any:
        return await self.repo.create(**kwargs)

    async def get_by_id(self, project_id: int) -> Optional[Any]:
        return await self.repo.get_by_id(project_id)

    async def get_by_user(self, user_id: int, limit: int = 10) -> List[Any]:
        return await self.repo.get_by_user(user_id, limit)

    async def update_status(self, project_id: int, status: str):
        await self.repo.update_status(project_id, status)

    async def delete(self, project_id: int) -> bool:
        return await self.repo.delete(project_id)

    async def count_by_user(self, user_id: int) -> int:
        return await self.repo.count_by_user(user_id)

    async def count_all(self) -> int:
        from sqlalchemy import select, func
        from database.models import Project
        result = await self.repo.db.execute(select(func.count(Project.project_id)))
        return result.scalar() or 0
