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
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

from ...core import Boat, listRoutingAlgorithms

class RoutingWizardDialog ():
	def create():
		return RoutingWizardDialog()

	def run(self):
		return self.dialog.run()

	def responseCancel(self, widget):
		self.dialog.response(Gtk.ResponseType.CANCEL)

	def destroy(self):
		return self.dialog.destroy()

	def drawPolar(self, widget, cr):
		if not self.polar:
			return

		#print (self.polar.speedTable)
		cr.set_source_rgb (1, 1, 1)
		cr.paint ()

		cr.set_line_width (0.3)
		cr.set_source_rgb (0, 0, 0)
		for x in self.polar.tws:# [::2]:
			cr.arc (0.0, 100.0, x * 3, math.radians (-180), math.radians (180.0))
			cr.stroke ()

		for x in self.polar.twa:# [::8]:
			cr.move_to (0.0, 100.0)
			cr.line_to (0 + math.sin (x) * 100.0, 100 + math.cos (x) * 100.0)
			cr.stroke ()

		cr.set_line_width (0.5)
		cr.set_source_rgb (1, 0, 0)

		for i in range (0, len (self.polar.tws), 1):
			for j in range (0, len (self.polar.twa), 1):
				cr.line_to (5 * self.polar.speedTable [j][i] * math.sin (self.polar.twa[j]), 100 + 5 * self.polar.speedTable [j][i] * math.cos (self.polar.twa[j]))
				cr.stroke ()
				cr.move_to (5 * self.polar.speedTable [j][i] * math.sin (self.polar.twa[j]), 100 + 5 * self.polar.speedTable [j][i] * math.cos (self.polar.twa[j]))



	def onBoatSelect(self, widget):
		this_dir, this_fn = os.path.split (__file__)
		bdir = self.boats [self.builder.get_object('boat-select').get_active ()]['dir']
		self.builder.get_object('boat-image').set_from_file(this_dir + '/../../data/boats/' + bdir + '/image.png')
		self.polar = Boat(bdir).polar
		self.builder.get_object('boat-polar-area').queue_draw()
		

	def __init__(self):
		self.polar = None

		this_dir, this_fn = os.path.split (__file__)
		self.boats = json.load (open (this_dir + '/../../data/boats/list.json'))

		self.builder = Gtk.Builder()
		self.builder.add_from_file("./gweatherrouting/ui/gtk/routingwizarddialog.glade")
		self.builder.connect_signals(self)

		self.dialog = self.builder.get_object('routing-wizard-dialog')
		self.dialog.set_default_size (550, 300)

		self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
		self.dialog.add_button("Run", Gtk.ResponseType.OK)


		boat_store = self.builder.get_object('boat-store')
		for boat in self.boats:
			boat_store.append ([boat['name']])
		self.builder.get_object('boat-select').set_active (0)


		routing_store = self.builder.get_object('routing-store')
		for r in listRoutingAlgorithms():
			routing_store.append ([r['name']])
		self.builder.get_object('routing-select').set_active (0)


		self.dialog.show_all ()
		self.dialog.run()


	def getSelectedAlgorithm (self):
		return listRoutingAlgorithms()[self.builder.get_object('routing-select').get_active ()]['class']


	def getSelectedBoat (self):
		return self.boats [self.builder.get_object('boat-select').get_active ()]['dir']


	def getInitialTime (self):
		return 0.0