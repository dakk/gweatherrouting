
import gi
import os
import json
import math
from threading import Thread
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject


class GribManagerWindow:
	def create(gribManager):
		return GribManagerWindow(gribManager)

	def show(self):
		self.window.show_all()

	def close(self):
		self.window.hide()

	def __init__(self, gribManager):
		self.gribManager = gribManager
		self.selectedGrib = None

		self.builder = Gtk.Builder()
		self.builder.add_from_file("./gweatherrouting/ui/gtk/gribmanagerwindow.glade")
		self.builder.connect_signals(self)

		self.window = self.builder.get_object('grib-manager-window')
		self.window.set_default_size (550, 300)

		self.gribFilesStore = self.builder.get_object("grib-files-store")
		self.gribManagerStore = self.builder.get_object("grib-manager-store")

		try:
			for x in self.gribManager.getDownloadList():
				self.gribFilesStore.append(x)			
		except:
			print ('Failed to download grib file list')

		for x in self.gribManager.gribs:
			self.gribManagerStore.append ([x.name, x.centre])

		# self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
		# self.dialog.add_button("Save", Gtk.ResponseType.OK)

		# self.dialog.show_all ()


	def onOpen(self, widget):
		pass


	def onGribDownloadPercentage (self, percentage):
		print ('Downloading grib: %d%% completed' % percentage)
		# self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Downloading grib: %d%% completed' % percentage)

	def onGribDownloadCompleted (self, status):
		self.gribManagerStore.clear()

		for x in self.gribManager.gribs:
			self.gribManagerStore.append ([x.name, x.centre])


	def onGribClick(self, widget, event):
		if event.button == 3:
			menu = self.builder.get_object("remote-grib-menu")
			menu.popup (None, None, None, None, event.button, event.time)


	def onGribSelect (self, selection):
		store, pathlist = selection.get_selected_rows()
		for path in pathlist:
			tree_iter = store.get_iter(path)
			self.selectedGrib = store.get_value(tree_iter, 4)
			print ('Selected: ', self.selectedGrib)

	def onGribDownload (self, widget):
		t = Thread(target=self.gribManager.download, args=(self.selectedGrib, self.onGribDownloadPercentage, self.onGribDownloadCompleted,))
		t.start ()