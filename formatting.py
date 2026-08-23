from typing import Dict, Any


def format_project_preview(data: Dict[str, Any]) -> str:
    """Format project data for preview message."""
    lines = []

    fields = [
        ("📦 ID", data.get("project_id")),
        ("🔥 Ниша", data.get("niche")),
        ("🎬 Тип", data.get("content_type")),
        ("🎨 Стиль", data.get("visual_style")),
        ("🖼 Режим", data.get("generation_mode")),
        ("⏱ Длительность", data.get("duration")),
        ("🌎 Язык", data.get("language")),
        ("🎙 Голос", data.get("voice")),
        ("🎭 Стиль голоса", data.get("voice_style")),
        ("📝 Субтитры", data.get("subtitles"))
    ]

    for label, value in fields:
        if value:
            lines.append(f"{label}: <b>{value}</b>")

    return "\n".join(lines)


def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable."""
    if seconds < 60:
        return f"{seconds} сек"
    mins = seconds // 60
    secs = seconds % 60
    return f"{mins} мин {secs} сек" if secs else f"{mins} мин"


def format_file_size(bytes_: int) -> str:
    """Format file size to human readable."""
    if bytes_ < 1024:
        return f"{bytes_} B"
    elif bytes_ < 1024 ** 2:
        return f"{bytes_ / 1024:.1f} KB"
    elif bytes_ < 1024 ** 3:
        return f"{bytes_ / (1024 ** 2):.1f} MB"
    else:
        return f"{bytes_ / (1024 ** 3):.1f} GB"


def safe_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
