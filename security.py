"""Security utilities."""

import re


def sanitize_input(text: str, max_length: int = 500) -> str:
    """Sanitize user input."""
    if not text:
        return ""
    text = str(text).strip()
    # Remove dangerous characters
    text = re.sub(r'[<>]', '', text)
    # Limit length
    if len(text) > max_length:
        text = text[:max_length]
    return text


def is_valid_user_id(user_id) -> bool:
    """Check if user ID is valid Telegram ID."""
    try:
        uid = int(user_id)
        return uid > 0
    except (ValueError, TypeError):
        return False


def is_valid_project_id(project_id) -> bool:
    """Check if project ID is valid."""
    try:
        pid = int(project_id)
        return pid > 0
    except (ValueError, TypeError):
        return False
