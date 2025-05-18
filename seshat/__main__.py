# -*- coding: utf-8 -*-

# Seshat: AI powered command palette
# Copyright (C) 2025 Joan Sala <contact@joansala.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import sys, traceback, gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, GLib
from seshat.application import Application


def handle_exception(exc_type, exc_value, exc_traceback):
    print("Unhandled exception:", exc_value, file=sys.stderr)
    traceback.print_exception(exc_type, exc_value, exc_traceback)
    app = Gtk.Application.get_default()
    GLib.idle_add(app.quit)


def main():
    sys.excepthook = handle_exception

    try:
        app = Application()
        exit_status = app.run(sys.argv)
        sys.exit(exit_status)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
