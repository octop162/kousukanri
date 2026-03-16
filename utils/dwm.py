"""Windows DWM API helpers for Fluent Design effects."""
import sys
import ctypes


def apply_fluent_effects(hwnd: int, dark: bool = True) -> None:
    """Apply Windows 11 Fluent Design effects to a window handle.

    Effects applied:
    - Dark / light title bar matching the app theme
    - Rounded window corners (Windows 11 native)
    - Mica material backdrop (Windows 11 22H2 / build 22621+)

    Silently ignored on non-Windows or older Windows builds.
    """
    if sys.platform != "win32":
        return

    try:
        dwmapi = ctypes.windll.dwmapi

        # Dark-mode title bar
        DWMWA_USE_IMMERSIVE_DARK_MODE = 20
        v = ctypes.c_int(1 if dark else 0)
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, ctypes.byref(v), ctypes.sizeof(v))

        # Rounded corners
        DWMWA_WINDOW_CORNER_PREFERENCE = 33
        DWMWCP_ROUND = 2
        v = ctypes.c_int(DWMWCP_ROUND)
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, ctypes.byref(v), ctypes.sizeof(v))

        # Mica material (22H2+)
        DWMWA_SYSTEMBACKDROP_TYPE = 38
        DWM_SYSTEMBACKDROP_MICA = 2
        v = ctypes.c_int(DWM_SYSTEMBACKDROP_MICA)
        dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, ctypes.byref(v), ctypes.sizeof(v))

    except Exception:
        pass
