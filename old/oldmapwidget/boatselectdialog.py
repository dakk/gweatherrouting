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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

from .polarwidget import PolarWidget
from ..core import polar


class BoatSelectDialog (Gtk.Dialog):
	def __init__(self, parent):
		this_dir, this_fn = os.path.split (__file__)
		self.boats = json.load (open (this_dir + '/../data/boats/list.json'))

		Gtk.Dialog.__init__(self, "Select a boat", parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
		self.set_default_size (450, 300)

		box = self.get_content_area ()

		boxcontent = Gtk.Box (orientation=Gtk.Orientation.HORIZONTAL)
		box.add (boxcontent)

		# Boat list
		boatStore = Gtk.ListStore (int, str)
		boatTree = Gtk.TreeView (boatStore)
		renderer = Gtk.CellRendererText ()
		boatTree.append_column (Gtk.TreeViewColumn("", renderer, text=0))
		boatTree.append_column (Gtk.TreeViewColumn("Boat", renderer, text=1))
		scbar = Gtk.ScrolledWindow ()
		scbar.set_hexpand (False)
		scbar.set_vexpand (True)
		scbar.add (boatTree)
		boxcontent.pack_start (scbar, True, True, 0)
		select = boatTree.get_selection ()
		select.connect ("changed", self.onBoatChanged)
		
		i = 0
		for boat in self.boats:
			boatStore.append ([i, boat['name']])
			i += 1

		# Boat info
		boxboat = Gtk.Box (orientation=Gtk.Orientation.VERTICAL)
		boxcontent.pack_start (boxboat, True, True, 0)

		self.boatName = Gtk.Label ('')
		boxboat.add (self.boatName)
		self.boatImage = Gtk.Image ()
		boxboat.add (self.boatImage)
		self.boatPolarContainer = Gtk.Box ()
		boxboat.add (self.boatPolarContainer)

		self.show_all ()
		self.selectBoat (0)

	def get_selected_boat (self):
		return self.selectedBoat

	def selectBoat (self, i):
		self.selectedBoat = self.boats[i]
		self.boatName.set_label (self.boats[i]['name'])
		self.boatImage.set_from_file (os.path.split (__file__)[0] + '/../data/boats/' + self.boats[i]['dir'] + '/image.png')
		
		for w in self.boatPolarContainer.get_children ():
			self.boatPolarContainer.remove (w)

		self.boatPolarContainer.add (PolarWidget (polar.Polar (os.path.split (__file__)[0] + '/../data/boats/' + self.boats[i]['dir'] + '/polar.pol')))
		self.boatPolarContainer.show_all ()
		
	def onBoatChanged (self, selection):
		model, treeiter = selection.get_selected()
		if treeiter != None:
			self.selectBoat (model[treeiter][0])
