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

import logging
from . import config
from .core.core import Core

logger = logging.getLogger ('regattasim')

def startUI ():
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk
    from .ui.mainwindow import MainWindow

    core = Core ()
    win = MainWindow (core)
    win.connect("delete-event", Gtk.main_quit)
    win.show_all()
    Gtk.main()

def stratCli ():
    return 0