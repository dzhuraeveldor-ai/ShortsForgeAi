"""
Database ORM models for AI Shorts Studio.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, Float, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.database import Base


class User(Base):
    """Telegram user model."""
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    last_active: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    blocked: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    unlimited: Mapped[bool] = mapped_column(Boolean, default=False)
    settings: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)

    projects: Mapped[list["Project"]] = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    limits: Mapped[list["Limit"]] = relationship("Limit", back_populates="user", cascade="all, delete-orphan")


class Limit(Base):
    """User usage limits with rolling 24-hour window."""
    __tablename__ = "limits"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    limit_type: Mapped[str] = mapped_column(String(32), index=True)  # ideas, scripts, hooks, images, videos, voice, subtitles, full_shorts, analysis
    count: Mapped[int] = mapped_column(Integer, default=0)
    last_reset: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="limits")


class Project(Base):
    """User project model."""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.user_id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(256), default="Untitled Short")
    status: Mapped[str] = mapped_column(String(32), default="draft")  # draft, generating, ready, failed, waiting_for_worker
    niche: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    content_type: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    visual_style: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    generation_method: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)  # images, video, images_to_video, auto
    duration: Mapped[int] = mapped_column(Integer, default=30)
    language: Mapped[str] = mapped_column(String(32), default="american_english")
    voice_gender: Mapped[str] = mapped_column(String(16), default="auto")
    voice_style: Mapped[str] = mapped_column(String(32), default="auto")
    subtitles: Mapped[bool] = mapped_column(Boolean, default=True)
    hook: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    idea: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    script: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    scenes: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    youtube_titles: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    youtube_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    youtube_hashtags: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    video_path: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    progress: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True, default=dict)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user: Mapped["User"] = relationship("User", back_populates="projects")
    jobs: Mapped[list["GenerationJob"]] = relationship("GenerationJob", back_populates="project", cascade="all, delete-orphan")


class GenerationJob(Base):
    """AI generation job for queue management."""
    __tablename__ = "generation_jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    job_type: Mapped[str] = mapped_column(String(32), index=True)  # text, image, video, voice, stt, editing, full
    status: Mapped[str] = mapped_column(String(32), default="queued")  # queued, processing, completed, failed, waiting_for_worker, cancelled
    payload: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    result: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    worker_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="jobs")


class AdminAction(Base):
    """Admin action log."""
    __tablename__ = "admin_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(64), index=True)
    target_user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    details: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Settings(Base):
    """Global bot settings."""
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
