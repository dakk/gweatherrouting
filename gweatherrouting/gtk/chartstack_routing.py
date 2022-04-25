# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
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

import traceback
import gi
from threading import Thread

gi.require_version('Gtk', '3.0')
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gdk, GObject

from .routingwizarddialog import RoutingWizardDialog
from .maplayers import IsochronesMapLayer
from ..core import RoutingTrack, utils
from weatherrouting import RoutingNoWindException

class ChartStackRouting:
	routingThread = None
	selectedRouting = None
	stopRouting = False

	def __init__(self):
		self.routingStore = self.builder.get_object("routing-store")

		self.isochronesMapLayer = IsochronesMapLayer ()
		self.map.layer_add (self.isochronesMapLayer)

		self.updateRoutings()

	def __del__(self): 
		if self.routingThread:
			self.stopRouting = True

	def onRoutingCreate(self, event):
		dialog = RoutingWizardDialog(self.core, self.parent)
		response = dialog.run ()

		polarFile = dialog.getSelectedPolar ()
		if response == Gtk.ResponseType.OK:
			self.stopRouting = False
			self.currentRouting = self.core.createRouting (dialog.getSelectedAlgorithm (), polarFile, dialog.getSelectedTrack(), dialog.getStartDateTime(), dialog.getSelectedStartPoint(), self.chartManager.getLinePointValidityProviders())
			self.currentRouting.name = 'routing-' + polarFile.split('.')[0]
			self.routingThread = Thread(target=self.onRoutingStep, args=())
			self.routingThread.start()
			self.builder.get_object("stop-routing-button").show()

		dialog.destroy ()
		
	def onRoutingStep (self):
		Gdk.threads_enter()
		self.progressBar.set_fraction(0.0)
		self.progressBar.set_text("0%")
		self.progressBar.show()
		Gdk.threads_leave()	

		res = None 

		while (not self.currentRouting.end) and (not self.stopRouting):
			try:
				res = self.currentRouting.step ()

			# This exception is not raised by the algorithm
			except RoutingNoWindException as e:
				Gdk.threads_enter()
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
				edialog.format_secondary_text ('Trying to create a route without wind information')
				edialog.run ()
				edialog.destroy ()
				self.progressBar.hide()
				Gdk.threads_leave()	
				self.isochronesMapLayer.setIsochrones ([], [])
				return None

			except Exception as e:			
				Gdk.threads_enter()
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
				edialog.format_secondary_text ('Error: ' + str(e))
				edialog.run ()
				edialog.destroy ()
				self.progressBar.hide()
				Gdk.threads_leave()	
				self.isochronesMapLayer.setIsochrones ([], [])
				traceback.print_exc()
				return None

			Gdk.threads_enter()
			self.progressBar.set_fraction(res.progress / 100.)
			self.progressBar.set_text(str(res.progress) + "%")

			self.isochronesMapLayer.setIsochrones (res.isochrones, res.path)
			self.timeControl.setTime(res.time)
			# self.map.queue_draw ()
			# self.builder.get_object('time-adjustment').set_value (res.time)
			Gdk.threads_leave()	

		if self.stopRouting:
			GObject.timeout_add (3000, self.progressBar.hide)
			self.builder.get_object("stop-routing-button").hide()
			return

		tr = []
		for wp in res.path:
			if len(wp) == 3:
				tr.append((wp[0], wp[1], str(wp[2]), 0, 0, 0, 0))
			else:
				tr.append((wp[0], wp[1], str(wp[4]), wp[5], wp[6], wp[7], wp[8]))

		Gdk.threads_enter()
		self.progressBar.set_fraction(1.0)
		self.progressBar.set_text("100%")
		GObject.timeout_add (3000, self.progressBar.hide)
		Gdk.threads_leave()

		self.core.trackManager.routings.append(RoutingTrack(name=utils.uniqueName(self.currentRouting.name, self.core.trackManager.routings), waypoints=tr, trackManager=self.core.trackManager))
		self.updateRoutings()
		self.builder.get_object("stop-routing-button").hide()


	def updateRoutings(self):
		self.routingStore.clear()

		for r in self.core.trackManager.routings:
			riter = self.routingStore.append(None, [r.name, '', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, r.visible, False, True])

			for x in r.waypoints:
				self.routingStore.append(riter, ['', x[2], x[0], x[1], x[3], x[4], x[5], x[6], False, True, False])

		self.map.queue_draw()
		self.core.trackManager.saveTracks()

	def onRoutingToggle(self, widget, i):
		self.core.trackManager.routings[int(i)].visible = not self.core.trackManager.routings[int(i)].visible
		self.updateRoutings()
		self.updateTrack()

	def onRoutingNameEdit(self, widget, i, name):
		self.core.trackManager.routings[int(i)].name = utils.uniqueName(name, self.core.trackManager.routings)
		self.updateRoutings()
		

	def onRoutingRemove(self, widget):
		self.core.trackManager.removeRouting(self.selectedRouting)
		self.updateRoutings()
		self.map.queue_draw()

	def onRoutingExport(self, widget):
		routing = self.core.trackManager.getRouting(self.selectedRouting)

		dialog = Gtk.FileChooserDialog ("Please select a destination", self.parent,
			Gtk.FileChooserAction.SAVE,
			(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

		filter_gpx = Gtk.FileFilter()
		filter_gpx.set_name("GPX track")
		filter_gpx.add_mime_type("application/gpx+xml")
		filter_gpx.add_pattern ('*.gpx')
		dialog.add_filter(filter_gpx)

		response = dialog.run ()

		if response == Gtk.ResponseType.OK:
			filepath = dialog.get_filename ()
			
			if not filepath.endswith('.gpx'):
				filepath += '.gpx'

			if routing.export (filepath):
				self.statusbar.push (self.statusbar.get_context_id ('Info'), 'Saved %d waypoints' % (len (routing)))
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Saved")
				edialog.format_secondary_text ('Saved %d waypoints' % (len (routing)))
				edialog.run ()
				edialog.destroy ()
			else:
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
				edialog.format_secondary_text ("Cannot save file: %s" % filepath)
				edialog.run ()
				edialog.destroy ()
			
		dialog.destroy ()


	def onRoutingStop (self, widget):
		self.stopRouting = True


	def onSelectRouting (self, selection):
		store, pathlist = selection.get_selected_rows()
		for path in pathlist:
			tree_iter = store.get_iter(path)
			value = store.get_value(tree_iter, 0)
			self.trackMapLayer.hightlightRouting(value)

			self.map.queue_draw()

			if path.get_depth() == 1:
				self.selectedRouting = value
			else:
				self.selectedRouting = None

	def onRoutingClick(self, item, event):		
		if self.selectedRouting != None and event.button == 3 and len(self.core.trackManager.routings) > 0:
			menu = self.builder.get_object("routing-item-menu")
			menu.popup (None, None, None, None, event.button, event.time)