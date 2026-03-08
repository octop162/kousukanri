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
        "ruler_text": "#CCCCCC",
    },
    "light": {
        "window": "#F0F0F0",
        "window_text": "#1E1E1E",
        "base": "#FFFFFF",
        "text": "#1E1E1E",
        "button": "#E0E0E0",
        "button_text": "#1E1E1E",
        "highlight": "#0078D7",
        "highlight_text": "#FFFFFF",
        "timeline_bg": "#F5F5F5",
        "ruler_major": "#BBBBBB",
        "ruler_minor": "#DDDDDD",
        "ruler_text": "#333333",
    },
    "pastel": {
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
        "ruler_text": "#7A6A60",
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
