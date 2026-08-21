"""
Admin panel handlers for AI Shorts Studio.
"""

from aiogram import Router, F
from aiogram.types import CallbackQuery
from loguru import logger

from database.repositories import UserRepository, ProjectRepository, JobRepository, AdminActionRepository
from database.models import User
from bot.keyboards import (
    admin_panel_keyboard, admin_stats_keyboard, back_to_menu_keyboard,
)
from bot.services.worker_client import worker_client
from bot.utils import escape_html, format_timestamp

router = Router()


async def handle_admin_callback(
    callback: CallbackQuery,
    user: User,
    user_repo: UserRepository,
    project_repo: ProjectRepository,
    job_repo: JobRepository,
) -> None:
    """Route admin panel callbacks."""
    _, args = callback.data.split(":", 1) if ":" in callback.data else ("admin", ["panel"])
    parts = args.split(":")
    action = parts[0]

    admin_action_repo = AdminActionRepository(callback.message.bot.db_session)

    if action == "panel":
        await _show_admin_panel(callback)

    elif action == "stats":
        period = parts[1] if len(parts) > 1 else None
        await _show_admin_stats(callback, period, user_repo, project_repo, job_repo)

    elif action == "users":
        await _show_users_list(callback, user_repo)

    elif action == "worker":
        await _show_worker_status(callback)

    elif action == "queue":
        await _show_queue_stats(callback, job_repo)

    elif action == "models":
        await _show_models_status(callback)

    elif action == "storage":
        await _show_storage_info(callback)

    elif action == "errors":
        await callback.answer("❌ Логи ошибок доступны в файлах logs/", show_alert=True)

    elif action in ["find_user", "block_user", "unblock_user", "give_limits", "reset_limits", "unlimited", "broadcast", "settings"]:
        await callback.answer(
            f"🔧 Функция «{action}» требует ввода данных.\n"
            f"Используйте: отправьте сообщение с нужным ID.",
            show_alert=True,
        )

    await callback.answer()


async def _show_admin_panel(callback: CallbackQuery) -> None:
    """Show admin panel."""
    await callback.message.edit_text(
        f"👑 <b>ADMIN PANEL</b>\n\n"
        f"Выберите раздел:",
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML",
    )


async def _show_admin_stats(
    callback: CallbackQuery,
    period: str | None,
    user_repo: UserRepository,
    project_repo: ProjectRepository,
    job_repo: JobRepository,
) -> None:
    """Show admin statistics."""
    if period is None:
        await callback.message.edit_text(
            f"📊 <b>Статистика</b>\n\n"
            f"Выберите период:",
            reply_markup=admin_stats_keyboard(),
            parse_mode="HTML",
        )
        return

    total_users = await user_repo.count_all()
    active_users = await user_repo.count_active(24)
    total_projects = await project_repo.count_all()
    total_jobs = await job_repo.count_all()
    queue_stats = await job_repo.get_queue_stats()

    period_names = {
        "today": "📅 Сегодня",
        "7d": "📅 7 дней",
        "30d": "📅 30 дней",
        "all": "📅 За всё время",
    }
    period_name = period_names.get(period, period)

    text = (
        f"📊 <b>Статистика — {period_name}</b>\n\n"
        f"👥 <b>Пользователи:</b>\n"
        f"   Всего: <b>{total_users}</b>\n"
        f"   Активные (24ч): <b>{active_users}</b>\n\n"
        f"🎬 <b>Проекты:</b>\n"
        f"   Всего: <b>{total_projects}</b>\n\n"
        f"🤖 <b>AI Jobs:</b>\n"
        f"   Всего: <b>{total_jobs}</b>\n"
        f"   В очереди: <b>{queue_stats.get('queued', 0)}</b>\n"
        f"   Обрабатываются: <b>{queue_stats.get('processing', 0)}</b>\n"
        f"   Завершено: <b>{queue_stats.get('completed', 0)}</b>\n"
        f"   Ошибки: <b>{queue_stats.get('failed', 0)}</b>\n"
        f"   Ожидают Worker: <b>{queue_stats.get('waiting_for_worker', 0)}</b>\n"
    )

    # Add period-specific keyboard
    await callback.message.edit_text(
        text,
        reply_markup=admin_stats_keyboard(),
        parse_mode="HTML",
    )


async def _show_users_list(
    callback: CallbackQuery,
    user_repo: UserRepository,
) -> None:
    """Show recent users list."""
    users = await user_repo.get_all(limit=15)
    total = await user_repo.count_all()

    text = f"👥 <b>Пользователи</b> (всего: {total})\n\n"

    for u in users:
        status_icon = "👑" if u.is_admin else "♾️" if u.unlimited else "🚫" if u.blocked else "👤"
        username = f"@{u.username}" if u.username else "—"
        text += (
            f"{status_icon} <code>{u.user_id}</code>\n"
            f"   {escape_html(u.first_name or '—')} | {username}\n"
            f"   📅 {format_timestamp(u.created_at)}\n\n"
        )

    text += "<i>Показаны последние 15 пользователей</i>"

    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML",
    )


async def _show_worker_status(callback: CallbackQuery) -> None:
    """Show AI Worker connection status."""
    health = await worker_client.health_check()

    if health.get("status") == "online":
        text = f"🤖 <b>AI Worker</b> — 🟢 <b>Online</b>\n\n"
        text += f"🖥 GPU: {health.get('gpu', 'N/A')}\n"
        text += f"💾 VRAM: {health.get('vram', 'N/A')}\n\n"
        text += f"<b>Доступные модели:</b>\n"

        models = health.get("models", {})
        if models:
            for model_name, available in models.items():
                icon = "✅" if available else "❌"
                text += f"   {icon} {model_name}\n"
        else:
            text += "   Информация о моделях недоступна\n"
    else:
        text = (
            f"🤖 <b>AI Worker</b> — 🔴 <b>Offline</b>\n\n"
            f"❌ Ошибка: {escape_html(str(health.get('error', 'Unknown')))}\n\n"
            f"Задачи будут сохранены со статусом WAITING_FOR_WORKER\n"
            f"и автоматически выполнятся после подключения Worker.\n\n"
            f"<i>Для запуска Worker:\n"
            f"<code>cd worker &amp;&amp; python main.py</code></i>"
        )

    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML",
    )


async def _show_queue_stats(
    callback: CallbackQuery,
    job_repo: JobRepository,
) -> None:
    """Show queue statistics."""
    stats = await job_repo.get_queue_stats()
    total = sum(stats.values())

    text = f"📋 <b>Очередь задач</b> (всего: {total})\n\n"

    status_icons = {
        "queued": "⏳",
        "processing": "⚙️",
        "completed": "✅",
        "failed": "❌",
        "waiting_for_worker": "⏸",
        "cancelled": "🚫",
    }

    for status, count in stats.items():
        icon = status_icons.get(status, "❓")
        text += f"{icon} <b>{status}:</b> {count}\n"

    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML",
    )


async def _show_models_status(callback: CallbackQuery) -> None:
    """Show AI models availability."""
    health = await worker_client.health_check()

    text = "🎨 <b>AI Модели</b>\n\n"

    if health.get("status") == "online":
        models = health.get("models", {})
        if models:
            for model_name, available in models.items():
                icon = "✅" if available else "❌"
                status_text = "Доступна" if available else "Не установлена"
                text += f"{icon} <b>{model_name}</b> — {status_text}\n"
        else:
            text += "Информация о моделях недоступна\n"
    else:
        text += (
            "🔴 Worker Offline — невозможно проверить модели.\n\n"
            "<b>Поддерживаемые модели:</b>\n"
            "✅ TEXT — Ollama (Qwen, Llama, Mistral)\n"
            "✅ IMAGE — SDXL / Stable Diffusion\n"
            "✅ VIDEO — Wan 2.1 / LTX-Video / CogVideoX\n"
            "✅ VOICE — Piper TTS / Kokoro\n"
            "✅ STT — Whisper\n"
            "✅ EDITING — FFmpeg\n"
        )

    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML",
    )


async def _show_storage_info(callback: CallbackQuery) -> None:
    """Show storage usage info."""
    import shutil
    from pathlib import Path

    from bot.config import config

    text = "💾 <b>Хранилище</b>\n\n"

    try:
        total, used, free = shutil.disk_usage("/")
        text += f"🖥 Диск системы:\n"
        text += f"   Всего: {_format_size(total)}\n"
        text += f"   Использовано: {_format_size(used)}\n"
        text += f"   Свободно: {_format_size(free)}\n\n"

        # Temp dir
        temp_size = _get_dir_size(config.TEMP_DIR)
        storage_size = _get_dir_size(config.STORAGE_DIR)
        logs_size = _get_dir_size(config.LOGS_DIR)

        text += f"📁 Проектные директории:\n"
        text += f"   temp/: {_format_size(temp_size)}\n"
        text += f"   storage/: {_format_size(storage_size)}\n"
        text += f"   logs/: {_format_size(logs_size)}\n"

    except Exception as e:
        text += f"❌ Ошибка получения информации: {escape_html(str(e))}"

    await callback.message.edit_text(
        text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML",
    )


def _format_size(size_bytes: int) -> str:
    """Format bytes to human readable."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"


def _get_dir_size(path: Path) -> int:
    """Calculate total directory size in bytes."""
    total = 0
    try:
        if path.exists():
            for item in path.rglob("*"):
                if item.is_file():
                    total += item.stat().st_size
    except Exception:
        pass
    return total
