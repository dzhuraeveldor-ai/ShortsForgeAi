"""
Command handlers for AI Shorts Studio bot.
Handles /start, /help, /w1ndeyz, /health commands.
"""

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from database.repositories import UserRepository, LimitRepository, ProjectRepository, JobRepository
from database.models import User
from bot.keyboards import (
    main_menu_keyboard, admin_panel_keyboard, back_to_menu_keyboard,
)
from bot.config import config
from bot.services.worker_client import worker_client
from bot.utils import is_admin, get_user_status, format_timestamp

router = Router()


# ============================================
# /start Command
# ============================================

@router.message(CommandStart())
async def cmd_start(
    message: Message,
    user: User,
    is_admin: bool,
    is_unlimited: bool,
    user_repo: UserRepository,
    limit_repo: LimitRepository,
    **kwargs,
) -> None:
    """Handle /start command - show main menu."""
    status = get_user_status(user.user_id, is_admin, is_unlimited)

    welcome_text = (
        f"🎬 <b>AI SHORTS STUDIO</b>\n\n"
        f"Добро пожаловать! Я создаю готовые вертикальные видео "
        f"для <b>YouTube Shorts</b> с помощью AI.\n\n"
        f"👤 <b>Ваш статус:</b> {status}\n\n"
        f"Просто выберите параметры, а AI сделает всё остальное:\n"
        f"• Придумает идею и Hook\n"
        f"• Напишет сценарий и разобьёт на сцены\n"
        f"• Создаст визуалы и озвучку\n"
        f"• Добавит субтитры и музыку\n"
        f"• Смонтирует готовый MP4\n"
        f"• Создаст YouTube SEO\n\n"
        f"Выберите действие ниже:"
    )

    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard(),
        parse_mode="HTML",
    )


# ============================================
# /help Command
# ============================================

@router.message(Command("help"))
async def cmd_help(message: Message, **kwargs) -> None:
    """Handle /help command."""
    help_text = (
        f"❓ <b>AI SHORTS STUDIO — Помощь</b>\n\n"
        f"<b>Как создать Short:</b>\n"
        f"1. Нажмите «🎬 Создать Short»\n"
        f"2. Выберите нишу, тип контента, визуальный стиль\n"
        f"3. Выберите способ генерации, длительность, язык, голос\n"
        f"4. Выберите Hook и идею\n"
        f"5. Подтвердите сценарий\n"
        f"6. AI автоматически создаст готовое видео\n\n"
        f"<b>Бесплатные лимиты (24ч):</b>\n"
        f"• Ideas: 10\n"
        f"• Scripts: 5\n"
        f"• Hooks: 10\n"
        f"• Images: 5\n"
        f"• AI Videos: 1\n"
        f"• Voice: 3\n"
        f"• Subtitles: 3\n"
        f"• Full Shorts: 1\n"
        f"• Analysis: 3\n\n"
        f"<b>Команды:</b>\n"
        f"/start — Главное меню\n"
        f"/help — Эта справка\n"
        f"/health — Проверить статус систем\n\n"
        f"<b>Важно:</b>\n"
        f"• Музыка выбирается автоматически под нишу\n"
        f"• Монтаж полностью автоматический\n"
        f"• Никаких платежей, всё бесплатно\n"
    )

    await message.answer(
        help_text,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )


# ============================================
# /health Command
# ============================================

@router.message(Command("health"))
async def cmd_health(message: Message, **kwargs) -> None:
    """Handle /health command - check system status."""
    status_text = "🩺 <b>Системный статус</b>\n\n"

    # Bot status
    status_text += "🤖 <b>Bot Server:</b> 🟢 Online\n"

    # Worker status
    worker_health = await worker_client.health_check()
    if worker_health.get("status") == "online":
        status_text += "⚙️ <b>AI Worker:</b> 🟢 Online\n"
        gpu = worker_health.get("gpu", "N/A")
        vram = worker_health.get("vram", "N/A")
        status_text += f"   GPU: {gpu}\n"
        status_text += f"   VRAM: {vram}\n"

        models = worker_health.get("models", {})
        status_text += "   Модели:\n"
        for model_name, available in models.items():
            icon = "✅" if available else "❌"
            status_text += f"   {icon} {model_name}\n"
    else:
        status_text += "⚙️ <b>AI Worker:</b> 🔴 Offline\n"
        status_text += f"   Ошибка: {worker_health.get('error', 'Unknown')}\n"
        status_text += "   Задачи будут сохранены и выполнены после подключения Worker.\n"

    # Database
    status_text += f"🗄 <b>Database:</b> 🟢 Connected\n"
    status_text += f"💾 <b>Low Resource Mode:</b> {'✅' if config.LOW_RESOURCE_MODE else '❌'}\n"

    await message.answer(
        status_text,
        reply_markup=back_to_menu_keyboard(),
        parse_mode="HTML",
    )


# ============================================
# /w1ndeyz Admin Command
# ============================================

@router.message(Command("w1ndeyz"))
async def cmd_admin(
    message: Message,
    user: User,
    is_admin: bool,
    **kwargs,
) -> None:
    """Handle /w1ndeyz admin command."""
    if not is_admin:
        logger.warning(f"Unauthorized admin attempt from user {user.user_id}")
        await message.answer("❌ Доступ запрещён.")
        return

    admin_text = (
        f"👑 <b>ADMIN PANEL</b>\n\n"
        f"Добро пожаловать, администратор!\n"
        f"Выберите действие:"
    )

    await message.answer(
        admin_text,
        reply_markup=admin_panel_keyboard(),
        parse_mode="HTML",
    )


# ============================================
# Main Menu Callback Handler
# ============================================

@router.callback_query(F.data.startswith("menu:"))
async def callback_menu(
    callback: CallbackQuery,
    user: User,
    is_admin: bool,
    is_unlimited: bool,
    project_repo: ProjectRepository,
    limit_repo: LimitRepository,
    **kwargs,
) -> None:
    """Handle main menu callbacks."""
    _, args = callback.data.split(":", 1) if ":" in callback.data else ("menu", ["main"])
    action = args.split(":")[0] if ":" in args else args

    if action == "main":
        status = get_user_status(user.user_id, is_admin, is_unlimited)
        text = (
            f"🎬 <b>AI SHORTS STUDIO</b>\n\n"
            f"👤 <b>Статус:</b> {status}\n\n"
            f"Выберите действие:"
        )
        await callback.message.edit_text(
            text,
            reply_markup=main_menu_keyboard(),
            parse_mode="HTML",
        )

    elif action == "create_short":
        # Delegate to workflow handler
        from bot.handlers.workflow import start_workflow
        await start_workflow(callback, user, is_unlimited, limit_repo)

    elif action == "projects":
        from bot.handlers.projects import show_projects
        await show_projects(callback, user, project_repo)

    elif action == "stats":
        from bot.handlers.projects import show_user_stats
        await show_user_stats(callback, user, limit_repo, project_repo)

    elif action == "help":
        help_text = (
            f"❓ <b>Помощь</b>\n\n"
            f"Нажмите «🎬 Создать Short» чтобы начать.\n"
            f"Выберите параметры, а AI сделает всё остальное.\n\n"
            f"Музыка и монтаж — полностью автоматические!\n\n"
            f"Команды:\n"
            f"/start — Главное меню\n"
            f"/help — Помощь\n"
            f"/health — Статус систем"
        )
        await callback.message.edit_text(
            help_text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )

    elif action == "settings":
        text = (
            f"⚙️ <b>Настройки</b>\n\n"
            f"🆔 Ваш ID: <code>{user.user_id}</code>\n"
            f"📅 Регистрация: {format_timestamp(user.created_at)}\n"
            f"🕐 Последняя активность: {format_timestamp(user.last_active)}\n"
            f"👑 Админ: {'Да' if is_admin else 'Нет'}\n"
            f"♾️ Безлимит: {'Да' if is_unlimited else 'Нет'}\n"
        )
        await callback.message.edit_text(
            text,
            reply_markup=back_to_menu_keyboard(),
            parse_mode="HTML",
        )

    elif action in ["ideas", "script", "hooks", "image", "video", "voice", "subtitles", "viral", "analyze", "seo"]:
        await callback.answer(
            f"🔄 Функция «{action}» доступна внутри полного рабочего процесса.\n"
            f"Нажмите «🎬 Создать Short» для начала.",
            show_alert=True,
        )

    await callback.answer()


# ============================================
# Admin Panel Callback Handler
# ============================================

@router.callback_query(F.data.startswith("admin:"))
async def callback_admin(
    callback: CallbackQuery,
    user: User,
    is_admin: bool,
    user_repo: UserRepository,
    project_repo: ProjectRepository,
    job_repo: JobRepository,
    **kwargs,
) -> None:
    """Handle admin panel callbacks."""
    if not is_admin:
        await callback.answer("❌ Доступ запрещён.", show_alert=True)
        return

    from bot.handlers.admin import handle_admin_callback
    await handle_admin_callback(
        callback, user, user_repo, project_repo, job_repo
    )
