from aiogram.fsm.state import StatesGroup, State


class CreateShortStates(StatesGroup):
    """FSM states for Create Short workflow."""
    choosing_niche = State()
    choosing_content_type = State()
    choosing_visual_style = State()
    choosing_generation_mode = State()
    choosing_duration = State()
    choosing_language = State()
    choosing_voice = State()
    choosing_voice_style = State()
    choosing_subtitles = State()
    preview = State()
