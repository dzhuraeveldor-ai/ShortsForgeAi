"""
Bot dependencies and middleware for AI Shorts Studio.
Provides database sessions, user context, etc.
"""

from typing import Any, Awaitable, Callable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update
from loguru import logger

from database.database import Database
from database.repositories import UserRepository, LimitRepository, ProjectRepository, JobRepository


class DatabaseMiddleware(BaseMiddleware):
    """Middleware that provides database session to handlers."""

    def __init__(self, db: Database):
        super().__init__()
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        async for session in self.db.session():
            data["db_session"] = session
            data["user_repo"] = UserRepository(session)
            data["limit_repo"] = LimitRepository(session)
            data["project_repo"] = ProjectRepository(session)
            data["job_repo"] = JobRepository(session)
            return await handler(event, data)


class UserMiddleware(BaseMiddleware):
    """Middleware that gets or creates user and checks blocks."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from aiogram.types import Message, CallbackQuery

        user_repo: UserRepository = data.get("user_repo")
        if not user_repo:
            return await handler(event, data)

        # Get Telegram user from event
        tg_user = None
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user

        if tg_user and not tg_user.is_bot:
            from bot.config import config
            is_admin = tg_user.id == config.ADMIN_ID and config.ADMIN_ID != 0

            user = await user_repo.get_or_create(
                user_id=tg_user.id,
                username=tg_user.username,
                first_name=tg_user.first_name,
                is_admin=is_admin,
            )

            data["user"] = user
            data["is_admin"] = is_admin or user.is_admin
            data["is_unlimited"] = data["is_admin"] or user.unlimited

            # Check if user is blocked
            if user.blocked:
                if isinstance(event, Message):
                    await event.answer("❌ Ваш аккаунт заблокирован.")
                elif isinstance(event, CallbackQuery):
                    await event.answer("❌ Ваш аккаунт заблокирован.", show_alert=True)
                return None

        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging updates."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from aiogram.types import Message, CallbackQuery

        if isinstance(event, Message):
            user = event.from_user
            logger.info(f"[MESSAGE] User {user.id} (@{user.username}): {event.text or '[media]'}")
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            logger.info(f"[CALLBACK] User {user.id} (@{user.username}): {event.data}")

        return await handler(event, data)
