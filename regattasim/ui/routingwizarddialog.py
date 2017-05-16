# -*- coding: utf-8 -*-
# Copyright (C) 2017 Davide Gessa
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

from ..core import grib, routing

class RoutingWizardDialog (Gtk.Dialog):
	def __init__(self, parent):
		this_dir, this_fn = os.path.split (__file__)
		self.boats = json.load (open (this_dir + '/../data/boats/list.json'))

		Gtk.Dialog.__init__(self, "Routing Wizard", parent, 0, (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OK, Gtk.ResponseType.OK))
		self.set_default_size (550, 300)

		box = self.get_content_area ()

		boxcontent = Gtk.Box (orientation=Gtk.Orientation.VERTICAL)
		box.add (boxcontent)

		## Boat select
		boxcontent.pack_start (Gtk.Label ('Boat'), False, False, 0)

		boat_store = Gtk.ListStore (str, str)
		for boat in self.boats:
			boat_store.append ([boat['dir'], boat['name']])

		self.boatSelect = Gtk.ComboBox.new_with_model_and_entry (boat_store)
		#name_combo.connect("changed", self.on_name_combo_changed)
		self.boatSelect.set_entry_text_column (1)
		self.boatSelect.set_active (0)
		boxcontent.pack_start (self.boatSelect, False, False, 0)


		## Routing algorithm select
		boxcontent.pack_start (Gtk.Label ('Routing algorithm'), False, False, 0)

		routing_store = Gtk.ListStore (str, object)
		for r in routing.ALGORITHMS:
			routing_store.append ([r['name'], r['class']])

		self.routingSelect = Gtk.ComboBox.new_with_model_and_entry (routing_store)
		#name_combo.connect("changed", self.on_name_combo_changed)
		self.routingSelect.set_entry_text_column (0)
		self.routingSelect.set_active (0)
		boxcontent.pack_start (self.routingSelect, False, False, 0)


		## Start time selector


		self.show_all ()


	def getSelectedAlgorithm (self):
		return routing.ALGORITHMS [self.routingSelect.get_active ()]['class']


	def getSelectedBoat (self):
		return self.boats [self.boatSelect.get_active ()]['dir']


	def getInitialTime (self):
		return 12.0