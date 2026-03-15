from PySide6.QtWidgets import QApplication, QStyleFactory
from PySide6.QtGui import QPalette, QColor


THEMES = {
    "dark": {
        "window": "#1E1E1E",
        "window_text": "#CCCCCC",
        "base": "#252526",
        "text": "#CCCCCC",
        "button": "#333333",
        "button_text": "#CCCCCC",
        "highlight": "#264F78",
        "highlight_text": "#FFFFFF",
        "timeline_bg": "#1E1E1E",
        "ruler_major": "#555555",
        "ruler_minor": "#333333",
        "ruler_sub_minor": "#2E2E2E",
        "ruler_text": "#CCCCCC",
        "timer_start": "#2ECC71",
        "timer_stop": "#E74C3C",
        "timer_add": "#3498DB",
        "drag_fill": "#FFFFFF",
        "drag_border": "#FFFFFF",
    },
    "sky": {
        "window": "#E3F2FD",
        "window_text": "#1A3A5C",
        "base": "#EBF5FF",
        "text": "#1A3A5C",
        "button": "#BBDEFB",
        "button_text": "#1A3A5C",
        "highlight": "#42A5F5",
        "highlight_text": "#FFFFFF",
        "timeline_bg": "#E3F2FD",
        "ruler_major": "#90CAF9",
        "ruler_minor": "#BBDEFB",
        "ruler_sub_minor": "#C5E2FA",
        "ruler_text": "#2C5F8A",
        "timer_start": "#2ECC71",
        "timer_stop": "#E74C3C",
        "timer_add": "#3498DB",
        "drag_fill": "#1565C0",
        "drag_border": "#0D47A1",
    },
    "light": {
        "window": "#FDF6F0",
        "window_text": "#5B4A42",
        "base": "#FFF8F3",
        "text": "#5B4A42",
        "button": "#F0E4DA",
        "button_text": "#5B4A42",
        "highlight": "#B8D8E8",
        "highlight_text": "#3A3A3A",
        "timeline_bg": "#FDF6F0",
        "ruler_major": "#D4C4B8",
        "ruler_minor": "#E8DDD4",
        "ruler_sub_minor": "#EDE1D8",
        "ruler_text": "#7A6A60",
        "timer_start": "#2ECC71",
        "timer_stop": "#E74C3C",
        "timer_add": "#3498DB",
        "drag_fill": "#5B4A42",
        "drag_border": "#3A2A22",
    },
    "black_green": {
        "window": "#0A0A0A",
        "window_text": "#00FF00",
        "base": "#0D0D0D",
        "text": "#00FF00",
        "button": "#1A1A1A",
        "button_text": "#00DD00",
        "highlight": "#00AA00",
        "highlight_text": "#000000",
        "timeline_bg": "#0A0A0A",
        "ruler_major": "#00AA00",
        "ruler_minor": "#004400",
        "ruler_sub_minor": "#003300",
        "ruler_text": "#00CC00",
        "timer_start": "#00CC00",
        "timer_stop": "#CC0000",
        "timer_add": "#00CC00",
        "drag_fill": "#00FF00",
        "drag_border": "#00CC00",
    },
    "monokai": {
        "window": "#272822",
        "window_text": "#F8F8F2",
        "base": "#1E1F1C",
        "text": "#F8F8F2",
        "button": "#3E3D32",
        "button_text": "#F8F8F2",
        "highlight": "#49483E",
        "highlight_text": "#A6E22E",
        "timeline_bg": "#272822",
        "ruler_major": "#75715E",
        "ruler_minor": "#3E3D32",
        "ruler_sub_minor": "#38372E",
        "ruler_text": "#F8F8F2",
        "timer_start": "#2ECC71",
        "timer_stop": "#E74C3C",
        "timer_add": "#3498DB",
        "drag_fill": "#A6E22E",
        "drag_border": "#F8F8F2",
    },
    "solarized_light": {
        "window": "#FDF6E3",
        "window_text": "#657B83",
        "base": "#EEE8D5",
        "text": "#586E75",
        "button": "#EEE8D5",
        "button_text": "#657B83",
        "highlight": "#268BD2",
        "highlight_text": "#FDF6E3",
        "timeline_bg": "#FDF6E3",
        "ruler_major": "#93A1A1",
        "ruler_minor": "#EEE8D5",
        "ruler_sub_minor": "#E4DEC8",
        "ruler_text": "#657B83",
        "timer_start": "#2ECC71",
        "timer_stop": "#E74C3C",
        "timer_add": "#3498DB",
        "drag_fill": "#268BD2",
        "drag_border": "#073642",
    },
    "solarized_dark": {
        "window": "#002B36",
        "window_text": "#839496",
        "base": "#073642",
        "text": "#93A1A1",
        "button": "#073642",
        "button_text": "#839496",
        "highlight": "#268BD2",
        "highlight_text": "#FDF6E3",
        "timeline_bg": "#002B36",
        "ruler_major": "#586E75",
        "ruler_minor": "#073642",
        "ruler_sub_minor": "#0A3D4D",
        "ruler_text": "#839496",
        "timer_start": "#2ECC71",
        "timer_stop": "#E74C3C",
        "timer_add": "#3498DB",
        "drag_fill": "#268BD2",
        "drag_border": "#839496",
    },
}


def get_theme_colors(theme_name: str) -> dict:
    """Return theme color dict. 'system' falls back to 'dark'."""
    if theme_name == "system":
        return _detect_system_theme()
    return THEMES.get(theme_name, THEMES["dark"])


def _detect_system_theme() -> dict:
    """Detect OS dark/light preference."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        )
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        winreg.CloseKey(key)
        return THEMES["light"] if value == 1 else THEMES["dark"]
    except Exception:
        return THEMES["dark"]


def apply_theme(app: QApplication, theme_name: str):
    """Apply a theme palette to the application.

    Uses the Fusion style so that palette settings are fully respected
    on all platforms (the native Windows style ignores custom palettes).
    """
    app.setStyle(QStyleFactory.create("Fusion"))

    colors = get_theme_colors(theme_name)

    palette = QPalette()
    role_map = {
        QPalette.ColorRole.Window: "window",
        QPalette.ColorRole.WindowText: "window_text",
        QPalette.ColorRole.Base: "base",
        QPalette.ColorRole.AlternateBase: "window",
        QPalette.ColorRole.Text: "text",
        QPalette.ColorRole.Button: "button",
        QPalette.ColorRole.ButtonText: "button_text",
        QPalette.ColorRole.Highlight: "highlight",
        QPalette.ColorRole.HighlightedText: "highlight_text",
        QPalette.ColorRole.ToolTipBase: "base",
        QPalette.ColorRole.ToolTipText: "text",
    }
    # Apply to all color groups (Active, Inactive, Disabled)
    for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive, QPalette.ColorGroup.Disabled):
        for role, key in role_map.items():
            palette.setColor(group, role, QColor(colors[key]))
        # PlaceholderText: semi-transparent text color
        placeholder = QColor(colors["text"])
        placeholder.setAlpha(128)
        palette.setColor(group, QPalette.ColorRole.PlaceholderText, placeholder)
        # Mid / Midlight for borders and separators
        palette.setColor(group, QPalette.ColorRole.Mid, QColor(colors["button"]).darker(120))
        palette.setColor(group, QPalette.ColorRole.Midlight, QColor(colors["button"]).lighter(120))

    app.setPalette(palette)
