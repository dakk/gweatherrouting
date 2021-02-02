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
import datetime
import math
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gio, GObject

import weatherrouting
from .timecontrol import TimeControl
from .timepickerdialog import TimePickerDialog

class RoutingWizardDialog:
	def create(core, parent):
		return RoutingWizardDialog(core, parent)

	def run(self):
		return self.dialog.run()

	def responseCancel(self, widget):
		self.dialog.response(Gtk.ResponseType.CANCEL)

	def destroy(self):
		return self.dialog.destroy()

		

	def __init__(self, core, parent):
		self.core = core
		self.polar = None

		self.boats = json.load (open (os.path.abspath(os.path.dirname(__file__)) + '/../../data/boats/list.json'))

		self.builder = Gtk.Builder()
		self.builder.add_from_file(os.path.abspath(os.path.dirname(__file__)) + "/routingwizarddialog.glade")
		self.builder.connect_signals(self)

		self.dialog = self.builder.get_object('routing-wizard-dialog')
		self.dialog.set_transient_for(parent)
		self.dialog.set_default_size (550, 300)

		self.dialog.add_button("Cancel", Gtk.ResponseType.CANCEL)
		self.dialog.add_button("Run", Gtk.ResponseType.OK)


		start_store = self.builder.get_object('start-store')
		start_store.append (['First track point', 'first-track-point'])
		start_store.append (['Boat position', 'boat-position'])

		for p in self.core.poiManager.pois:
			start_store.append (['POI: ' + p.name, 'poi-' + p.name])
		self.builder.get_object('start-select').set_active (0)


		boat_store = self.builder.get_object('boat-store')
		for boat in self.boats:
			boat_store.append ([boat['name']])
		self.builder.get_object('boat-select').set_active (0)


		routing_store = self.builder.get_object('routing-store')
		for r in weatherrouting.listRoutingAlgorithms():
			routing_store.append ([r['name']])
		self.builder.get_object('routing-select').set_active (0)

		track_store = self.builder.get_object('track-store')
		for r in self.core.trackManager.tracks:
			track_store.append ([r.name])
		self.builder.get_object('track-select').set_active (0)

		self.builder.get_object('time-entry').set_text(datetime.datetime.today().strftime(TimeControl.DFORMAT))

		self.dialog.show_all ()

	def onRoutingAlgoSelect(self, widget):
		ralgo = weatherrouting.listRoutingAlgorithms()[self.builder.get_object('routing-select').get_active ()]['class']

		if len(ralgo.PARAMS.keys()) == 0:
			self.builder.get_object('router-params').hide()
			return 

		
		cont = self.builder.get_object('router-params-container')
		
		for x in cont.get_children():
			cont.remove(x)

		box = Gtk.VBox()
		cont.add(box)

		self.paramWidgets = {}

		for x in ralgo.PARAMS:
			p = ralgo.PARAMS[x]
			cb = Gtk.HBox()
			
			cb.add(Gtk.Label(p.name))

			if p.ttype == 'float':
				adj = Gtk.Adjustment(value=p.value, step_incr=p.step, page_incr=p.step*10.0, lower=p.lower, upper=p.upper)
				e = Gtk.SpinButton(adjustment=adj, digits=p.digits)
			elif p.ttype == 'int':
				adj = Gtk.Adjustment(value=p.value, step_incr=p.step, page_incr=p.step*10.0, lower=p.lower, upper=p.upper)
				e = Gtk.SpinButton(adjustment=adj, digits=0)
				
			e.set_tooltip_text(p.tooltip)
			e.connect('changed', self.onParamChange)
			self.paramWidgets[e] = p
			cb.add(e)

			box.add(cb)

		self.builder.get_object('router-params').show_all()

	def onParamChange(self, widget):
		p = self.paramWidgets[widget]
		p.value = float(widget.get_text())

	def onBoatSelect(self, widget):
		bdir = self.boats [self.builder.get_object('boat-select').get_active ()]['dir']
		boatPath = os.path.abspath(os.path.dirname(__file__)) + '/../../data/boats/' + bdir
		self.builder.get_object('boat-image').set_from_file(boatPath + '/image.png')
		self.polar = weatherrouting.Polar (boatPath + '/polar.pol')
		self.builder.get_object('boat-polar-area').queue_draw()

	def onTimeSelect(self, widget):
		tp = TimePickerDialog.create(self.dialog)
		tp.setDateTime(self.builder.get_object('time-entry').get_text())
		response = tp.run()

		if response == Gtk.ResponseType.OK:
			self.builder.get_object('time-entry').set_text(tp.getDateTime().strftime(TimeControl.DFORMAT))
		
		tp.destroy()


	def getStartDateTime(self):
		return datetime.datetime.strptime(self.builder.get_object('time-entry').get_text(), TimeControl.DFORMAT)

	def getSelectedTrack (self):
		return self.core.trackManager.tracks[self.builder.get_object('track-select').get_active ()]

	def getSelectedAlgorithm (self):
		return weatherrouting.listRoutingAlgorithms()[self.builder.get_object('routing-select').get_active ()]['class']

	def getSelectedBoat (self):
		return self.boats [self.builder.get_object('boat-select').get_active ()]['dir']


	def getSelectedStartPoint (self):
		s = self.builder.get_object('start-select').get_active ()
		if s == 0:
			return None 
		elif s == 1:
			if self.core.boatInfo.isValid():
				return [self.core.boatInfo.latitude, self.core.boatInfo.longitude]
			else:
				return None
		else:
			s -= 2
			return self.core.poiManager.pois[s].position



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


