"""
Worker utilities.
"""

import random
import string
from pathlib import Path


def generate_id(length: int = 12) -> str:
    """Generate a random alphanumeric ID."""
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def ensure_dir(path: Path) -> Path:
    """Ensure directory exists, creating it if needed."""
    path.mkdir(parents=True, exist_ok=True)
    return path
