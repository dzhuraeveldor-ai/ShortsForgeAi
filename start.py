from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.keyboards.main import get_main_keyboard
from bot.services.user_service import UserService
from database.database import get_db_session
from sqlalchemy.ext.asyncio import AsyncSession

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, db: AsyncSession):
    """Handle /start command — register user and show main menu."""
    user_service = UserService(db)

    # Register or update user
    user = await user_service.get_or_create(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )

    is_new = user.created_at == user.updated_at  # Simplified check

    if is_new:
        welcome_text = (
            "👋 <b>Добро пожаловать в ShortsForge AI!</b>\n\n"
            "Я помогу тебе автоматически создавать вертикальные видео для YouTube Shorts.\n\n"
            "🎬 <b>Что я умею:</b>\n"
            "• Генерировать идеи и сценарии\n"
            "• Создавать изображения и видео\n"
            "• Делать озвучку и субтитры\n"
            "• Подбирать музыку и звуковые эффекты\n"
            "• Монтировать готовое MP4 9:16\n\n"
            "Нажми кнопку ниже, чтобы начать! 👇"
        )
    else:
        welcome_text = (
            f"👋 С возвращением, <b>{message.from_user.first_name or 'друг'}</b>!\n\n"
            "Выбери действие в меню ниже 👇"
        )

    await message.answer(
        welcome_text,
        reply_markup=get_main_keyboard(message.from_user.id)
    )


@router.callback_query(F.data == "menu:main")
async def callback_main_menu(callback: CallbackQuery, db: AsyncSession):
    """Return to main menu."""
    await callback.message.edit_text(
        "🏠 <b>Главное меню</b>\n\nВыбери действие 👇",
        reply_markup=get_main_keyboard(callback.from_user.id)
    )
    await callback.answer()
