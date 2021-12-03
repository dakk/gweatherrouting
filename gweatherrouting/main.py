# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
'''
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
'''

# Fix for python-for-android relative imports
import sys
sys.path.append("..")
sys.path.append("...")

import logging
from . import log
from .core import Core
from .conn import ConnManager


logger = logging.getLogger ('gweatherrouting')


def initCore():
    conn = ConnManager()
    conn.plugAll()
    conn.startPolling()
    core = Core(conn)
    return core, conn

def startUIKivy ():
    from .ui.kivy.app import GWeatherRoutingApp
    core, conn = initCore()
    GWeatherRoutingApp(core, conn).run()

def startUIGtk ():
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from .ui.gtk.mainwindow import MainWindow

    core, conn = initCore()

    MainWindow.create(core, conn)
    Gtk.main()


if __name__ == "__main__":
    startUIKivy()