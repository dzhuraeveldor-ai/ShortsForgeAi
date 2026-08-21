import os
from dataclasses import dataclass

@dataclass
class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "ТУТ_ТОКЕН_ТВОЕГО_БОТА")
    API_ID: int = int(os.getenv("API_ID", 0))
    API_HASH: str = os.getenv("API_HASH", "")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///shorts.db")

config = Config()
