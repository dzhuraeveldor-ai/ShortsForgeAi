"""
Workflow state manager for the short creation process.
Stores user's current workflow state in memory.
"""

from typing import Optional, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


@dataclass
class WorkflowState:
    """Represents the current state of a user's short creation workflow."""
    user_id: int
    step: str = "idle"  # idle, niche, ctype, vstyle, genmethod, duration, lang, vgender, vstyle_voice, subs, hook, idea, script, preview, generating
    niche: Optional[str] = None
    custom_niche: Optional[str] = None
    content_type: Optional[str] = None
    visual_style: Optional[str] = None
    generation_method: Optional[str] = None
    duration: int = 30
    language: str = "american_english"
    voice_gender: str = "auto"
    voice_style: str = "auto"
    subtitles: bool = True
    hooks: list = field(default_factory=list)
    selected_hook: Optional[str] = None
    ideas: list = field(default_factory=list)
    selected_idea: Optional[str] = None
    script: Optional[str] = None
    scenes: list = field(default_factory=list)
    project_id: Optional[int] = None
    progress_message_id: Optional[int] = None
    current_stage: int = 0
    total_stages: int = 10
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        data = asdict(self)
        data["created_at"] = self.created_at.isoformat()
        data["last_updated"] = self.last_updated.isoformat()
        return data

    def update(self, **kwargs) -> None:
        """Update state fields."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_updated = datetime.utcnow()

    def get_effective_niche(self) -> str:
        """Get custom niche if set, otherwise standard niche."""
        return self.custom_niche or self.niche or "general"

    def preview_text(self) -> str:
        """Generate preview text for user confirmation."""
        niche_display = self.custom_niche if self.custom_niche else self.niche
        gen_method_display = {
            "images": "🖼 Images",
            "video": "🎥 AI Video",
            "images_to_video": "🔄 Images → Video",
            "auto": "🎲 Automatic",
        }.get(self.generation_method, self.generation_method)

        return (
            f"🎬 <b>Project Preview</b>\n\n"
            f"<b>Niche:</b> {niche_display}\n"
            f"<b>Content Type:</b> {self.content_type}\n"
            f"<b>Visual:</b> {self.visual_style}\n"
            f"<b>Generation:</b> {gen_method_display}\n"
            f"<b>Duration:</b> {self.duration} sec\n"
            f"<b>Language:</b> {self.language}\n"
            f"<b>Voice:</b> {self.voice_gender}\n"
            f"<b>Voice Style:</b> {self.voice_style}\n"
            f"<b>Subtitles:</b> {'✅ Yes' if self.subtitles else '❌ No'}"
        )


class WorkflowManager:
    """Manages workflow states for all active users."""

    def __init__(self):
        self._states: dict[int, WorkflowState] = {}

    def get(self, user_id: int) -> WorkflowState:
        """Get or create workflow state for user."""
        if user_id not in self._states:
            self._states[user_id] = WorkflowState(user_id=user_id)
        return self._states[user_id]

    def set(self, user_id: int, state: WorkflowState) -> None:
        """Set workflow state for user."""
        self._states[user_id] = state

    def reset(self, user_id: int) -> None:
        """Reset user's workflow state."""
        if user_id in self._states:
            del self._states[user_id]

    def cleanup_old(self, max_age_hours: int = 24) -> int:
        """Clean up old workflow states."""
        now = datetime.utcnow()
        to_remove = []
        for user_id, state in self._states.items():
            if (now - state.last_updated).total_seconds() > max_age_hours * 3600:
                to_remove.append(user_id)
        for user_id in to_remove:
            del self._states[user_id]
        return len(to_remove)

    def active_count(self) -> int:
        """Get number of active workflows."""
        return len(self._states)


# Global workflow manager instance
workflow_manager = WorkflowManager()
