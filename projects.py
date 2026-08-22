from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List, Any


def get_projects_keyboard(projects: List[Any]) -> InlineKeyboardMarkup:
    """Projects list keyboard."""
    buttons = []

    status_emoji = {
        "draft": "📝", "queued": "⏳", "processing": "⚙️",
        "ready": "✅", "failed": "❌", "waiting_for_worker": "⏸",
        "cancelled": "🚫"
    }

    for p in projects:
        emoji = status_emoji.get(p.status, "❓")
        niche = p.niche or "Без ниши"
        text = f"{emoji} #{p.project_id} — {niche[:25]}"
        buttons.append([
            InlineKeyboardButton(text=text, callback_data=f"project:{p.project_id}")
        ])

    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_project_actions_keyboard(
    project_id: int,
    status: str,
    output_path: str = None
) -> InlineKeyboardMarkup:
    """Project actions keyboard."""
    buttons = []

    if status == "ready" and output_path:
        buttons.append([
            InlineKeyboardButton(
                text="📥 Скачать видео",
                callback_data=f"project_download:{project_id}"
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            text="🔄 Обновить статус",
            callback_data=f"project_refresh:{project_id}"
        ),
        InlineKeyboardButton(
            text="🗑 Удалить",
            callback_data=f"project_delete:{project_id}"
        )
    ])

    buttons.append([InlineKeyboardButton(text="⬅️ К списку", callback_data="menu:projects")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)
