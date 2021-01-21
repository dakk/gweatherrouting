
import gi
import os
import json
import math
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject


class SettingsWindow:
	def create(parent, settingsManager):
		return SettingsWindow(parent, settingsManager)

	def show(self):
		self.window.show_all()

	def close(self):
		self.window.hide()

	def __init__(self, mainWindow, settingsManager):
		self.mainWindow = mainWindow
		self.settingsManager = settingsManager

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/settingswindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object('settings-window')
		self.window.set_default_size (550, 300)


		self.chartStore = self.builder.get_object("chart-store")

		for name in self.mainWindow.chartManager.charts:
			x = self.mainWindow.chartManager.charts[name]
			self.chartStore.append ([name, x.path, x.enabled, x.ctype])


		# self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
		# self.dialog.add_button("Save", Gtk.ResponseType.OK)

		# self.dialog.show_all ()