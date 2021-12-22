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
from .settingswindow_charts import SettingsWindowCharts
from .settingswindow_connections import SettingsWindowConnections
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject, Gdk
from threading import Thread


class SettingsWindow(SettingsWindowConnections, SettingsWindowCharts):
	def __init__(self, mainWindow, settingsManager):
		self.mainWindow = mainWindow
		self.settingsManager = settingsManager

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/settingswindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object('settings-window')
		self.window.set_default_size (550, 300)

		# self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
		# self.dialog.add_button("Save", Gtk.ResponseType.OK)

		# self.dialog.show_all ()

		self.builder.get_object('grib-arrow-opacity-adjustment').set_value(self.settingsManager.grib.arrowOpacity)

		SettingsWindowConnections.__init__(self, mainWindow, settingsManager)
		SettingsWindowCharts.__init__(self, mainWindow, settingsManager)

	def show(self):
		self.window.show_all()	
		self.builder.get_object("ais-tab").hide()
		self.builder.get_object("general-tab").hide()

	def close(self):
		self.window.hide()
		
	def onGribArrowOpacityChange(self, v):
		self.settingsManager.grib.arrowOpacity = v.get_value()

