import gi
import os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

from ..core import grib

class GribSelectDialog (Gtk.Dialog):
	def __init__(self, parent):
		Gtk.Dialog.__init__(self, "Select a grib file", parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
		self.set_default_size (550, 300)

		box = self.get_content_area ()

		boxcontent = Gtk.Box (orientation=Gtk.Orientation.HORIZONTAL)
		box.add (boxcontent)


		gribStore = Gtk.ListStore (str, str, str, str, str)
		gribTree = Gtk.TreeView (gribStore)
		renderer = Gtk.CellRendererText ()
		gribTree.append_column (Gtk.TreeViewColumn("Filename", renderer, text=0))
		gribTree.append_column (Gtk.TreeViewColumn("Provider", renderer, text=1))
		gribTree.append_column (Gtk.TreeViewColumn("Date", renderer, text=2))
		gribTree.append_column (Gtk.TreeViewColumn("Size", renderer, text=3))
		gribTree.append_column (Gtk.TreeViewColumn("Uri", renderer, text=4))
		scbar = Gtk.ScrolledWindow ()
		scbar.set_hexpand (False)
		scbar.set_vexpand (True)
		scbar.add (gribTree)
		boxcontent.pack_start (scbar, True, True, 0)
		select = gribTree.get_selection ()
		select.connect ("changed", self.onGribChanged)
		
		for x in grib.Grib.getDownloadList ():
			gribStore.append (x)

		self.show_all ()


	def onGribChanged (self, selection):
		model, treeiter = selection.get_selected()
		if treeiter != None:
			self.selectedGrib = model[treeiter][-1]

	def get_selected_grib (self):
		return self.selectedGrib