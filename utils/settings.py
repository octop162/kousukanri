import json
import sys
from pathlib import Path

_IS_COMPILED = "__compiled__" in globals()


def _get_data_dir() -> Path:
    """Return the data directory: next to exe if Nuitka-compiled, else ~/.tracker/."""
    if _IS_COMPILED:
        return Path(sys.executable).parent / "data"
    return Path.home() / ".tracker"


DATA_DIR = _get_data_dir()
SETTINGS_DIR = DATA_DIR
SETTINGS_FILE = SETTINGS_DIR / "settings.json"

DEFAULTS = {
    "snap_minutes": 1,
    "shift_snap_minutes": 5,
    "ctrl_snap_minutes": 10,
    "default_duration_minutes": 30,
    "theme": "dark",
    "timeline_start_hour": 7,
    "timeline_end_hour": 22,
    "api_server_enabled": False,
    "api_port": 8321,
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
