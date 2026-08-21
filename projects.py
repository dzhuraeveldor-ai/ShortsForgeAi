"""
Projects and user stats handlers for AI Shorts Studio.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

from database.repositories import LimitRepository, ProjectRepository
from database.models import User
from bot.keyboards import (
    projects_list_keyboard, project_detail_keyboard,
    back_to_menu_keyboard, main_menu_keyboard,
)
from bot.utils import escape_html, format_timestamp, format_duration

router = Router()


async def show_projects(
    callback: CallbackQuery,
    user: User,
    project_repo: ProjectRepository,
    page: int = 0,
) -> None:
    """Show user's projects list."""
    projects = await project_repo.get_by_user(user.user_id, offset=page * 10, limit=10)
    total = await project_repo.count_by_user(user.user_id)

    if not projects:
        await callback.message.edit_text(
            f"📁 <b>Мои проекты</b>\n\n"
            f"У вас пока нет проектов.\n"
            f"Нажмите «🎬 Создать Short» чтобы начать!",
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )
        await callback.answer()
        return

    text = f"📁 <b>Мои проекты</b> (всего: {total})\n\n"

    status_icons = {
        "draft": "📝",
        "generating": "⏳",
        "ready": "✅",
        "failed": "❌",
        "waiting_for_worker": "⏸",
    }

    for p in projects:
        icon = status_icons.get(p.status, "📄")
        text += (
            f"{icon} <b>#{p.id}</b> — {escape_html(p.title[:40])}\n"
            f"   📅 {format_timestamp(p.created_at)} | ⏱ {p.duration}s\n"
            f"   Статус: {p.status}\n\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=projects_list_keyboard(projects, page),
        parse_mode="HTML",
    )
    await callback.answer()


async def show_user_stats(
    callback: CallbackQuery,
    user: User,
    limit_repo: LimitRepository,
    project_repo: ProjectRepository,
) -> None:
    """Show user's usage statistics."""
    limits = await limit_repo.get_all(user.user_id)
    total_projects = await project_repo.count_by_user(user.user_id)

    text = f"📊 <b>Ваша статистика</b>\n\n"
    text += f"📁 Всего проектов: <b>{total_projects}</b>\n\n"
    text += f"📋 <b>Лимиты на 24 часа:</b>\n"

    limit_names = {
        "ideas": "💡 Ideas",
        "scripts": "✍️ Scripts",
        "hooks": "🪝 Hooks",
        "images": "🖼 Images",
        "videos": "🎥 Videos",
        "voice": "🎙 Voice",
        "subtitles": "📝 Subtitles",
        "full_shorts": "🎬 Full Shorts",
        "analysis": "🔍 Analysis",
    }

    for limit_type, info in limits.items():
        name = limit_names.get(limit_type, limit_type)
        used = info["used"]
        max_lim = info["max"]
        remaining = info["remaining"]
        pct = (used / max_lim * 100) if max_lim > 0 else 0
        bar = "█" * int(pct / 10) + "░" * (10 - int(pct / 10))
        text += f"{name}: {bar} {used}/{max_lim} (осталось: {remaining})\n"

    text += (
        f"\n<i>Лимиты обновляются автоматически каждые 24 часа "
        f"по скользящему окну.</i>"
    )

    await callback.message.edit_text(
        text,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("project:"))
async def callback_project(
    callback: CallbackQuery,
    user: User,
    project_repo: ProjectRepository,
    **kwargs,
) -> None:
    """Handle project detail callbacks."""
    _, args = callback.data.split(":", 1) if ":" in callback.data else ("project", [""])
    parts = args.split(":")
    action = parts[0] if parts else "view"

    if action == "view" and len(parts) > 1:
        try:
            project_id = int(parts[1])
            project = await project_repo.get_by_id(project_id)

            if not project or project.user_id != user.user_id:
                await callback.answer("❌ Проект не найден", show_alert=True)
                return

            status_display = {
                "draft": "📝 Черновик",
                "generating": "⏳ Генерация",
                "ready": "✅ Готов",
                "failed": "❌ Ошибка",
                "waiting_for_worker": "⏸ Ожидает Worker",
            }.get(project.status, project.status)

            text = (
                f"📄 <b>Проект #{project.id}</b>\n\n"
                f"<b>Название:</b> {escape_html(project.title)}\n"
                f"<b>Статус:</b> {status_display}\n"
                f"<b>Ниша:</b> {escape_html(project.niche or '-')}\n"
                f"<b>Тип:</b> {escape_html(project.content_type or '-')}\n"
                f"<b>Стиль:</b> {escape_html(project.visual_style or '-')}\n"
                f"<b>Длительность:</b> {format_duration(project.duration)}\n"
                f"<b>Язык:</b> {project.language}\n"
                f"<b>Субтитры:</b> {'✅' if project.subtitles else '❌'}\n"
                f"<b>Создан:</b> {format_timestamp(project.created_at)}\n"
                f"<b>Обновлён:</b> {format_timestamp(project.updated_at)}\n"
            )

            if project.error_message:
                text += f"\n❌ <b>Ошибка:</b> {escape_html(project.error_message[:200])}\n"

            await callback.message.edit_text(
                text,
                reply_markup=project_detail_keyboard(project.id, project.status),
                parse_mode="HTML",
            )

        except ValueError:
            await callback.answer("❌ Неверный ID проекта", show_alert=True)

    elif action == "delete" and len(parts) > 1:
        try:
            project_id = int(parts[1])
            project = await project_repo.get_by_id(project_id)

            if project and project.user_id == user.user_id:
                await project_repo.delete(project_id)
                await callback.answer("🗑 Проект удалён", show_alert=True)
                await show_projects(callback, user, project_repo)
            else:
                await callback.answer("❌ Проект не найден", show_alert=True)

        except ValueError:
            await callback.answer("❌ Неверный ID", show_alert=True)

    elif action == "download" and len(parts) > 1:
        await callback.answer(
            "📥 Для скачивания требуется запущенный AI Worker.\n"
            "Смотрите README.md для инструкций.",
            show_alert=True,
        )

    elif action == "regenerate" and len(parts) > 1:
        await callback.answer(
            "🔄 Регенерация запустится после подключения Worker.",
            show_alert=True,
        )

    elif action == "edit" and len(parts) > 1:
        await callback.answer(
            "✏️ Редактирование проектов в разработке.",
            show_alert=True,
        )

    await callback.answer()


@router.callback_query(F.data.startswith("projects:"))
async def callback_projects_nav(
    callback: CallbackQuery,
    user: User,
    project_repo: ProjectRepository,
    **kwargs,
) -> None:
    """Handle projects pagination."""
    _, args = callback.data.split(":", 1) if ":" in callback.data else ("projects", ["page:0"])
    parts = args.split(":")

    if parts[0] == "page" and len(parts) > 1:
        try:
            page = max(0, int(parts[1]))
            await show_projects(callback, user, project_repo, page)
        except ValueError:
            await show_projects(callback, user, project_repo, 0)
