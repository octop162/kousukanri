import sys
import os
import winreg
from pathlib import Path

APP_NAME = "KousuKanri"
_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def get_app_executable_path():
    # Nuitkaでコンパイルされているかどうかの判定
    is_nuitka = "__compiled__" in globals()

    if is_nuitka:
        # ビルド済みEXEとして動いている場合
        # sys.executable は実行されている .exe のフルパスを指します
        return os.path.abspath(sys.argv[0])
    else:
        # スクリプト(.py)として開発環境で動いている場合
        # 開発中は python.exe が登録されても良い、あるいは警告を出す
        return os.path.abspath(__file__)

# スタートアップ登録用の文字列作成
def _exe_path() -> str:
    exe_path = get_app_executable_path()
    return f'"{exe_path}" --minimized'


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
