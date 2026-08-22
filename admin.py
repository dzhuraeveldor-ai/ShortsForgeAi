from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_keyboard() -> InlineKeyboardMarkup:
    """Admin panel keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats"),
            InlineKeyboardButton(text="🖥 Worker статус", callback_data="admin:worker")
        ],
        [
            InlineKeyboardButton(text="📦 Очередь", callback_data="admin:queue")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")
        ]
    ])
