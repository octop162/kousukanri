import json
import os
from pathlib import Path

# Settings file path: ~/.tracker/settings.json
SETTINGS_DIR = Path.home() / ".tracker"
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

DEFAULTS = {
    "snap_minutes": 1,
    "default_duration_minutes": 30,
    "theme": "dark",
    "timeline_start_hour": 7,
    "timeline_end_hour": 22,
}


def load_settings() -> dict:
    """Load settings from JSON, falling back to defaults."""
    settings = dict(DEFAULTS)
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            settings.update(data)
        except (json.JSONDecodeError, OSError):
            pass
    return settings


def save_settings(settings: dict):
    """Save settings to JSON."""
    SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)
