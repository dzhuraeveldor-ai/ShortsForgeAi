from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Simple back button keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=callback_data)]
    ])


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Simple cancel button keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❌ Отмена", callback_data="common:cancel")]
    ])
