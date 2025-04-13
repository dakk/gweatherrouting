# -*- coding: utf-8 -*-
# Copyright (C) 2017-2025 Davide Gessa
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
# flake8: noqa: E402
import logging
import os

import gi

gi.require_version("Gtk", "3.0")
try:
    gi.require_version("OsmGpsMap", "1.2")
except:
    gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gtk

logger = logging.getLogger("gweatherrouting")


class RegattaStack(Gtk.Box):
    def __init__(self, parent, chartManager, core):
        Gtk.Widget.__init__(self)

        self.parent = parent
        self.core = core

        # self.core.connectionManager.connect("data", self.dataHandler)

        self.builder = Gtk.Builder()
        self.builder.add_from_file(
            os.path.abspath(os.path.dirname(__file__)) + "/regattastack.glade"
        )
        self.builder.connect_signals(self)
        self.pack_start(self.builder.get_object("regattacontent"), True, True, 0)

        self.statusBar = self.builder.get_object("statusbar")

        self.map = self.builder.get_object("map")
        self.map.set_center_and_zoom(39.0, 9.0, 6)
        # self.map.layer_add (chartManager)
        # self.chartManager.addMap(self.map)

        self.show_all()
