
import gi
import os
import json
import math
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



	# Grib
	# def onGribDownloadPercentage (self, percentage):
	# 	self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Downloading grib: %d%% completed' % percentage)

	# def onGribDownloadCompleted (self, status):
	# 	if status:
	# 		edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Done")
	# 		edialog.format_secondary_text ("Grib downloaded successfully")
	# 		edialog.run ()
	# 		edialog.destroy ()	
	# 	else:
	# 		edialog = Gtk.MessageDialog (self.window, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
	# 		edialog.format_secondary_text ("Error during grib download")
	# 		edialog.run ()
	# 		edialog.destroy ()	


	# def onGribSelect (self, widget):
	# 	dialog = GribSelectDialog (self.window)
	# 	response = dialog.run()

	# 	if response == Gtk.ResponseType.OK:
	# 		selectedGrib = dialog.get_selected_grib ()
	# 		t = Thread(target=self.core.grib.download, args=(selectedGrib, self.onGribDownloadPercentage, self.onGribDownloadCompleted,))
	# 		t.start ()
	# 	elif response == Gtk.ResponseType.CANCEL:
	# 		pass

	# 	dialog.destroy()