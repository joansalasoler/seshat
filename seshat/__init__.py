# -*- coding: utf-8 -*-


import gi
gi.require_version("Gtk", "4.0")
from gi.repository import GLib
from pathlib import Path

APP_ID = "com.joansala.Seshat"
APP_NAME = "seshat"

BASE_DIR = Path(__file__).resolve().parent
CONFIG_DIR = Path(GLib.get_user_config_dir()) / APP_NAME
RESOURCES_DIR = BASE_DIR / "resources"

__version__ = "0.1.0"
