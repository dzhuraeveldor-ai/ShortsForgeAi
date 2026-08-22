from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from typing import List


def _build_grid(items: List[str], prefix: str, cols: int = 2) -> InlineKeyboardMarkup:
    """Build inline keyboard grid from items."""
    buttons = []
    row = []

    for item in items:
        row.append(InlineKeyboardButton(
            text=item,
            callback_data=f"{prefix}:{item}"
        ))
        if len(row) == cols:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    # Add back button
    buttons.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="menu:main")])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_niche_keyboard(niches: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(niches, "niche", cols=2)


def get_content_type_keyboard(types: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(types, "ctype", cols=2)


def get_visual_style_keyboard(styles: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(styles, "style", cols=2)


def get_generation_mode_keyboard(modes: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(modes, "genmode", cols=1)


def get_duration_keyboard(durations: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(durations, "dur", cols=2)


def get_language_keyboard(languages: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(languages, "lang", cols=1)


def get_voice_keyboard(voices: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(voices, "voice", cols=1)


def get_voice_style_keyboard(styles: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(styles, "vstyle", cols=2)


def get_subtitles_keyboard(options: List[str]) -> InlineKeyboardMarkup:
    return _build_grid(options, "subs", cols=1)


def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Confirm generation keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Generate!", callback_data="confirm:generate"),
            InlineKeyboardButton(text="❌ Cancel", callback_data="confirm:cancel")
        ]
    ])
