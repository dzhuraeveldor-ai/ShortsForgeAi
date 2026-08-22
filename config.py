from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Worker configuration loaded from .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Application
    APP_VERSION: str = "1.0.0"
    WORKER_ID: str = "default_worker"

    # API Server
    WORKER_HOST: str = "0.0.0.0"
    WORKER_PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./bot.db"

    # Queue limits
    MAX_QUEUE_SIZE: int = 20

    # Directories
    TEMP_DIR: str = "./temp"
    STORAGE_DIR: str = "./storage"
    LOG_DIR: str = "./logs"

    # Resource mode
    LOW_RESOURCE_MODE: bool = True

    # Development
    DEV_MODE: bool = False


# Global settings instance
settings = Settings()
