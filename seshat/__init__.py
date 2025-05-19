# -*- coding: utf-8 -*-


import sys, gi
gi.require_version("Gtk", "4.0")
from gi.repository import GLib
from pathlib import Path
from .i18n import setup_locale

APP_ID = "com.joansala.Seshat"
APP_NAME = "seshat"

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path(GLib.get_user_config_dir()) / APP_NAME
RESOURCES_DIR = BASE_DIR / "resources"
LOCALES_DIR = BASE_DIR / "locales"

try:
    setup_locale(APP_NAME, str(LOCALES_DIR))
except Exception as e:
    message = f"Error setting up localization: {str(e)}"
    print(message, file=sys.stderr)

__version__ = "0.1.0"
