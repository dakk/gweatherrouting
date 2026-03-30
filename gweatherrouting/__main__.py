# -*- coding: utf-8 -*-
# Copyright (C) 2017-2026 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""

import logging
import signal

from gweatherrouting import log  # noqa: F401
from gweatherrouting.core import Core

logger = logging.getLogger("gweatherrouting")


def start_ui_gtk():
    import gi

    gi.require_version("Gtk", "3.0")
    from gi.repository import GLib, Gtk

    from gweatherrouting.gtk.mainwindow import MainWindow

    main_window = MainWindow(Core())

    # Let GLib handle SIGINT so Ctrl+C triggers a clean shutdown
    def on_sigint():
        main_window.quit(None, None)
        return GLib.SOURCE_REMOVE

    GLib.unix_signal_add(GLib.PRIORITY_DEFAULT, signal.SIGINT, on_sigint)

    Gtk.main()


if __name__ == "__main__":
    start_ui_gtk()
