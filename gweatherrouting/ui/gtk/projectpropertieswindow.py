
import gi
import os
import json
import math
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

class ProjectPropertiesWindow:
	def create():
		return ProjectPropertiesWindow()

	def show(self):
		self.window.show_all()
	
	def close(self):
		self.window.hide()
		
	def __init__(self):
		self.builder = Gtk.Builder()
		self.builder.add_from_file("./gweatherrouting/ui/gtk/projectpropertieswindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object('project-properties-window')
		self.window.set_default_size (550, 300)

		# self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
		# self.dialog.add_button("Save", Gtk.ResponseType.OK)
