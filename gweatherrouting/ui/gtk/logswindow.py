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
import json
import math
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

class LogsWindow(Gtk.Window):		
	def __init__(self, chartManager):
		Gtk.Window.__init__(self, title="Logs")
		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/logscontent.glade")
		self.builder.connect_signals(self)

		self.set_default_size (550, 300)

		self.add(self.builder.get_object("logscontent"))

		self.show_all()

		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		self.map.layer_add (chartManager)

		self.graph_area = self.builder.get_object("graph_area")

	
