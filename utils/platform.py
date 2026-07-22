"""Platform-safe font and path resolution."""
import configparser
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


def get_app_version():
    """Read the installed package version on Android or buildozer.spec on desktop."""
    if _platform == "android":
        try:
            from jnius import autoclass
            activity = autoclass("org.kivy.android.PythonActivity").mActivity
            info = activity.getPackageManager().getPackageInfo(
                activity.getPackageName(), 0)
            return str(info.versionName)
        except Exception:
            return "?"
    try:
        parser = configparser.ConfigParser()
        parser.read(os.path.join(_APP_DIR, "buildozer.spec"), encoding="utf-8")
        return parser.get("app", "version", fallback="?")
    except Exception:
        return "?"

def is_android():
    return _platform == "android"

def is_ios():
    return _platform == "ios"

def is_desktop():
    return _platform not in ("android", "ios")
