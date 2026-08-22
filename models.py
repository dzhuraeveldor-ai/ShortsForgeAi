from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """Пользователь Telegram."""
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())
    last_active = Column(DateTime)
    blocked = Column(Boolean, default=False)
    is_unlimited = Column(Boolean, default=False)


class Project(Base):
    """Проект — содержит все параметры создаваемого шортса."""
    __tablename__ = "projects"

    project_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    niche = Column(String(100))
    content_type = Column(String(50))
    status = Column(String(30), default="new", index=True)
    duration = Column(Integer, default=30)
    language = Column(String(50), default="American English")
    visual_style = Column(String(100))
    voice = Column(String(100))
    voice_style = Column(String(100))
    subtitles = Column(String(20), default="yes")
    generation_mode = Column(String(30), default="images")
    hook = Column(Text)
    idea = Column(Text)
    script = Column(JSON)
    scenes = Column(JSON)
    output_path = Column(String(500))
    completed_stages = Column(JSON, default=dict)
    seo_data = Column(JSON, default=dict)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class GenerationJob(Base):
    """Задача на генерацию — ставится в очередь Worker'у."""
    __tablename__ = "generation_jobs"

    job_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.project_id"), nullable=True)
    type = Column(String(50), nullable=False)
    status = Column(String(30), default="queued", index=True)
    priority = Column(Integer, default=0)
    parameters = Column(JSON)
    progress = Column(JSON, default=dict)
    result_data = Column(JSON)
    error = Column(Text)
    attempts = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now(), index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class WorkerStatus(Base):
    """Статус подключённых AI Worker'ов."""
    __tablename__ = "worker_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    worker_id = Column(String(100), unique=True, nullable=False)
    status = Column(String(30))
    last_seen = Column(DateTime, server_default=func.now(), onupdate=func.now())
    hardware_info = Column(JSON)
    capabilities = Column(JSON)


class ModelStatus(Base):
    """Статус доступности AI моделей."""
    __tablename__ = "model_status"

    id = Column(Integer, primary_key=True, autoincrement=True)
    category = Column(String(50), index=True)
    model_name = Column(String(100))
    available = Column(Boolean, default=False)
    details = Column(JSON)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class UsageEvent(Base):
    """События использования для подсчёта лимитов."""
    __tablename__ = "usage_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    operation_type = Column(String(50), index=True)
    created_at = Column(DateTime, server_default=func.now(), index=True)


class UserSettings(Base):
    """Настройки пользователя."""
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, unique=True, nullable=False, index=True)
    default_language = Column(String(50), default="American English")
    default_voice = Column(String(100), default="automatic")
    default_voice_style = Column(String(100), default="automatic")
    default_subtitles = Column(String(20), default="yes")
    default_visual_style = Column(String(100), default="realistic")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class AdminAction(Base):
    """Лог действий администратора."""
    __tablename__ = "admin_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, nullable=False, index=True)
    action = Column(String(100))
    target_user_id = Column(Integer)
    details = Column(JSON)
    created_at = Column(DateTime, server_default=func.now())
