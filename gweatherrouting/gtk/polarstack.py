# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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
from .widgets.polar import PolarWidget

logger = logging.getLogger ('gweatherrouting')


class PolarStack(Gtk.Box):		
	def __init__(self, parent, core):
		Gtk.Widget.__init__(self)

		self.parent = parent
		self.core = core

		# self.core.connectionManager.connect("data", self.dataHandler)

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/polarstack.glade")
		self.builder.connect_signals(self)
		self.pack_start(self.builder.get_object("polarcontent"), True, True, 0)

		self.statusBar = self.builder.get_object("statusbar")


		self.polarWidget = PolarWidget(self.parent)
		self.polarWidget.loadPolar('first317.pol')
		self.builder.get_object("polar-text").get_buffer().set_text(self.polarWidget.polar.toString())
		self.builder.get_object('polarwidgetcontainer').pack_start(self.polarWidget, True, True, 0)

		self.show_all()
