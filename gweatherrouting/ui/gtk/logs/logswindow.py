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

from gweatherrouting.ui.gtk.logs.logdata import LogData
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject


class LogsWindow(Gtk.Window):		
	def __init__(self, chartManager, connManager):
		Gtk.Window.__init__(self, title="Logs")

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/logscontent.glade")
		self.builder.connect_signals(self)

		self.set_default_size (800, 600)

		self.add(self.builder.get_object("logscontent"))

		self.show_all()


		self.map = self.builder.get_object("map")
		self.map.set_center_and_zoom (39., 9., 6)
		self.map.layer_add (chartManager)

		self.graph_area = self.builder.get_object("graph_area")
		self.logData = LogData(connManager, self.graph_area, self.map)


	
	def onLoadClick(self, widget):
		dialog = Gtk.FileChooserDialog ("Please choose a file", self,
					Gtk.FileChooserAction.OPEN,
					(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
			
		filter_nmea = Gtk.FileFilter ()		
		filter_nmea.set_name ("NMEA log")
		# filter_nmea.add_mime_type ("application/gpx+xml")
		filter_nmea.add_pattern ('*.nmea')
		dialog.add_filter (filter_nmea)

		# filter_gpx = Gtk.FileFilter ()		
		# filter_gpx.set_name ("GPX track file")
		# filter_gpx.add_mime_type ("application/gpx+xml")
		# filter_gpx.add_pattern ('*.gpx')
		# dialog.add_filter (filter_gpx)

		response = dialog.run()
		
		if response == Gtk.ResponseType.OK:
			filepath = dialog.get_filename ()
			dialog.destroy ()

			try:
				self.logData.loadFromFile(filepath)
			except Exception as e:
				print(e)
				edialog = Gtk.MessageDialog (self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.CANCEL, "Error")
				edialog.format_secondary_text ("Cannot open file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
		else:
			dialog.destroy()


	def onGraphDraw(self, widget, cr):
		self.logData.draw(widget, cr)