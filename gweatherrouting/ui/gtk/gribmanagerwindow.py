
import gi
import os
import json
import math
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

# Sections: grib, nmea, gps, chart

class GribManagerWindow:
	def create():
		return GribManagerWindow()

	def show(self):
		self.window.show_all()


	def __init__(self):
		self.builder = Gtk.Builder()
		self.builder.add_from_file("./gweatherrouting/ui/gtk/gribmanagerwindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object('grib-manager-window')
		self.window.set_default_size (550, 300)

		# self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
		# self.dialog.add_button("Save", Gtk.ResponseType.OK)

		# self.dialog.show_all ()