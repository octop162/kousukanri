import sys
import winreg

APP_NAME = "KousuKanri"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _exe_path() -> str:
    return f'"{sys.executable}" --minimized'


def is_startup_enabled() -> bool:
    """レジストリにスタートアップ登録があるか確認。"""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY)
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except OSError:
        return False


def set_startup(enabled: bool):
    """スタートアップ登録をON/OFFする。"""
    key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE
    )
    if enabled:
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _exe_path())
    else:
        try:
            winreg.DeleteValue(key, APP_NAME)
        except OSError:
            pass
    winreg.CloseKey(key)
