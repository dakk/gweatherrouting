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

import gi
import os

gi.require_version('OsmGpsMap', '1.2')
gi.require_version('Gtk', '3.0')
gi.require_version('Dazzle', '1.0')

from gi.repository import Gtk
import logging

logger = logging.getLogger ('gweatherrouting')


class RegattaStack(Gtk.Box):		
	def __init__(self, parent, chartManager, connManager):
		Gtk.Widget.__init__(self)

		self.parent = parent
		self.conn = connManager

		# self.conn.connect("data", self.dataHandler)

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/regattastack.glade")
		self.builder.connect_signals(self)
		self.pack_start(self.builder.get_object("regattacontent"), True, True, 0)

		self.statusBar = self.builder.get_object("statusbar")

		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		# self.map.layer_add (chartManager)

		self.show_all()
