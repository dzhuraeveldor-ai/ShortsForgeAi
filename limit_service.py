from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from bot.config import bot_settings
from database.repositories import UsageEventRepository


class LimitService:
    """Service for checking and enforcing usage limits."""

    # Map operation types to config limits
    LIMIT_MAP = {
        "ideas": "LIMIT_IDEAS",
        "scripts": "LIMIT_SCRIPTS",
        "hooks": "LIMIT_HOOKS",
        "images": "LIMIT_IMAGES",
        "videos": "LIMIT_VIDEOS",
        "voice": "LIMIT_VOICE",
        "subtitles": "LIMIT_SUBTITLES",
        "shorts": "LIMIT_SHORTS",
        "analysis": "LIMIT_ANALYSIS"
    }

    def __init__(self, db: AsyncSession):
        self.repo = UsageEventRepository(db)

    def get_limit(self, operation: str) -> int:
        """Get limit value for operation."""
        attr = self.LIMIT_MAP.get(operation)
        if not attr:
            return 999
        return getattr(bot_settings, attr, 999)

    async def can_use(self, user_id: int, operation: str) -> bool:
        """Check if user can use this operation (within 24h limit)."""
        limit = self.get_limit(operation)
        if limit <= 0:
            return True  # Unlimited

        used = await self.repo.count_events_24h(user_id, operation)
        return used < limit

    async def record_usage(self, user_id: int, operation: str):
        """Record usage event (after successful completion)."""
        await self.repo.add_event(user_id, operation)

    async def get_usage_info(self, user_id: int, operation: str) -> Dict[str, Any]:
        """Get detailed usage info for operation."""
        limit = self.get_limit(operation)
        used = await self.repo.count_events_24h(user_id, operation)
        remaining = max(0, limit - used)
        return {
            "operation": operation,
            "limit": limit,
            "used": used,
            "remaining": remaining,
            "window": "24 hours",
            "unlimited": limit <= 0
        }

    async def get_all_limits(self, user_id: int) -> Dict[str, Dict[str, Any]]:
        """Get usage info for all operations."""
        result = {}
        for op in self.LIMIT_MAP:
            result[op] = await self.get_usage_info(user_id, op)
        return result
