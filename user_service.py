from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from datetime import datetime

from database.models import User


class UserService:
    """Service for managing users."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create(
        self,
        user_id: int,
        username: str = None,
        first_name: str = None,
        last_name: str = None
    ) -> User:
        """Get existing user or create new."""
        result = await self.db.execute(
            select(User).where(User.user_id == user_id)
        )
        user = result.scalar_one_or_none()

        if user:
            # Update user info
            user.username = username
            user.first_name = first_name
            user.last_name = last_name
            user.last_active = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(user)
            return user

        # Create new user
        user = User(
            user_id=user_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            last_active=datetime.utcnow(),
            blocked=False,
            is_unlimited=False
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        return await self.db.get(User, user_id)

    async def count_all(self) -> int:
        from sqlalchemy import func
        result = await self.db.execute(select(func.count(User.user_id)))
        return result.scalar() or 0
