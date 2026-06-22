"""Platform-safe font and path resolution."""
import os
from kivy.utils import platform as _platform
from kivy.app import App

_APP_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FONT_DIR = os.path.join(_APP_DIR, "assets", "fonts")


def _data_dir():
    if _platform == "android":
        app = App.get_running_app()
        if app:
            return app.user_data_dir
        return "/sdcard/Android/data/org.fitness.fitnessapp/files"
    return _APP_DIR

_ANDROID_CJK_PATHS = [
    "/system/fonts/NotoSansCJK-Regular.ttc",
    "/system/fonts/DroidSansFallback.ttf",
    "/system/fonts/NotoSansSC-Regular.otf",
]

def _find_android_font():
    for path in _ANDROID_CJK_PATHS:
        if os.path.exists(path):
            return path
    return None

def get_font_path(filename):
    if _platform == "android":
        system_font = _find_android_font()
        if system_font:
            return system_font
    return os.path.join(_FONT_DIR, filename)

def get_symbol_font_path():
    return os.path.join(_FONT_DIR, "roboto_regular.ttf")

def get_db_path():
    return os.path.join(_data_dir(), "fitness.db")

def is_android():
    return _platform == "android"

def is_ios():
    return _platform == "ios"

def is_desktop():
    return _platform not in ("android", "ios")
