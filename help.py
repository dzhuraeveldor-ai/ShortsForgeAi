from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from bot.keyboards.common import get_back_keyboard

router = Router(name="help")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command."""
    text = (
        "📖 <b>Помощь по ShortsForge AI</b>\n\n"
        "<b>🎬 Как создать шортс:</b>\n"
        "1. Нажми «🎬 Create Short» в главном меню\n"
        "2. Выбери нишу, тип контента, визуальный стиль\n"
        "3. Укажи длительность, язык и голос\n"
        "4. Подтверди — AI начнёт генерацию\n"
        "5. Получи готовое MP4 + SEO (заголовки, описание, хештеги)\n\n"
        "<b>🎵 Музыка и звуки:</b>\n"
        "Подбираются автоматически по нише. Только CC0/Royalty-Free.\n\n"
        "<b>⏱ Лимиты:</b>\n"
        "Действуют 24 часа с момента использования.\n\n"
        "<b>👑 Админ-команда:</b> /admin"
    )
    await message.answer(text, reply_markup=get_back_keyboard("menu:main"))


@router.callback_query(F.data == "menu:help")
async def callback_help(callback: CallbackQuery):
    """Help section from menu."""
    text = (
        "📖 <b>Помощь</b>\n\n"
        "<b>Основные команды:</b>\n"
        "/start — главное меню\n"
        "/help — справка\n"
        "/projects — мои проекты\n"
        "/admin — админ-панель\n\n"
        "<b>Процесс создания:</b>\n"
        "1. Выбор параметров\n"
        "2. AI генерирует контент\n"
        "3. Автоматический монтаж\n"
        "4. Готовое видео + SEO"
    )
    await callback.message.edit_text(
        text,
        reply_markup=get_back_keyboard("menu:main")
    )
    await callback.answer()
