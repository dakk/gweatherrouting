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
import logging
from threading import Thread
import gi

from ..core.geo.routing import Routing

gi.require_version('Gtk', '3.0')
try:
	gi.require_version('OsmGpsMap', '1.2')
except:
	gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gdk, GObject
from weatherrouting import RoutingNoWindException

from .routingwizarddialog import RoutingWizardDialog
from .maplayers import IsochronesMapLayer
from ..core import utils
from .. import log

logger = logging.getLogger ('gweatherrouting')

class ChartStackRouting:
	routingThread = None
	selectedRouting = None
	stopRouting = False

	def __init__(self):
		self.currentRouting = None
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
			self.currentRouting = self.core.createRouting (dialog.getSelectedAlgorithm (), polarFile,
				dialog.getSelectedTrack(), dialog.getStartDateTime(), dialog.getSelectedStartPoint(),
				self.chartManager.getLinePointValidityProviders(), not dialog.getCoastlineChecks())
			self.currentRouting.name = 'routing-' + polarFile.split('.')[0]
			self.routingThread = Thread(target=self.onRoutingStep, args=())
			self.routingThread.start()
			self.builder.get_object("stop-routing-button").show()

		dialog.destroy ()

	def onRoutingStep (self):
		Gdk.threads_enter()
		self.progressBar.set_fraction(1.0)
		self.progressBar.set_text("1%")
		self.progressBar.show()
		Gdk.threads_leave()

		res = None

		while (not self.currentRouting.end) and (not self.stopRouting):
			try:
				res = self.currentRouting.step ()
				logger.debug ("Routing step: %s", str(res))

			# This exception is not raised by the algorithm
			except RoutingNoWindException as _:
				Gdk.threads_enter()
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
				edialog.format_secondary_text ('Trying to create a route without wind information')
				edialog.run ()
				edialog.destroy ()
				self.progressBar.hide()
				Gdk.threads_leave()
				self.isochronesMapLayer.setIsochrones ([], [])
				self.builder.get_object("stop-routing-button").hide()
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
				self.builder.get_object("stop-routing-button").hide()
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
			Gdk.threads_enter()
			GObject.timeout_add (3000, self.progressBar.hide)
			self.builder.get_object("stop-routing-button").hide()
			self.isochronesMapLayer.setIsochrones ([], [])
			Gdk.threads_leave()
			return

		tr = []
		for wp in res.path:
			tr.append((wp.pos[0], wp.pos[1], wp.time.strftime("%m/%d/%Y, %H:%M:%S"), wp.twd, wp.tws, wp.speed, wp.brg))

		Gdk.threads_enter()
		self.progressBar.set_fraction(1.0)
		self.progressBar.set_text("100%")
		GObject.timeout_add (3000, self.progressBar.hide)
		Gdk.threads_leave()

		self.core.routingManager.append(Routing(name=self.core.routingManager.getUniqueName(self.currentRouting.name),
				points=tr, isochrones=res.isochrones, collection=self.core.routingManager))
		self.updateRoutings()
		self.builder.get_object("stop-routing-button").hide()


	def updateRoutings(self):
		self.routingStore.clear()

		for r in self.core.routingManager:
			riter = self.routingStore.append(None, [r.name, '', 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, r.visible, False, True])

			for x in r:
				self.routingStore.append(riter, ['', x[2], x[0], x[1], x[3], x[4], x[5], x[6], False, True, False])

		self.map.queue_draw()
		self.core.trackManager.save()

	def onRoutingToggle(self, widget, i):
		self.core.routingManager[int(i)].visible = not self.core.routingManager[int(i)].visible
		self.updateRoutings()
		self.updateTrack()

	def onRoutingNameEdit(self, widget, i, name):
		self.core.routingManager[int(i)].name = utils.uniqueName(name, self.core.routingManager)
		self.updateRoutings()

	def onRoutingRemove(self, widget):
		self.core.routingManager.removeByName(self.selectedRouting)
		self.updateRoutings()
		self.map.queue_draw()

	def onRoutingExport(self, widget):
		routing = self.core.routingManager.getByName(self.selectedRouting)

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
				self.statusbar.push (self.statusbar.get_context_id ('Info'), f'Saved {len (routing)} waypoints')
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.INFO, Gtk.ButtonsType.OK, "Saved")
				edialog.format_secondary_text (f'Saved {len (routing)} waypoints')
				edialog.run ()
				edialog.destroy ()
			else:
				edialog = Gtk.MessageDialog (self.parent, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK, "Error")
				edialog.format_secondary_text (f"Cannot save file: {filepath}")
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

				routing = self.core.routingManager.getByName(self.selectedRouting)
				self.isochronesMapLayer.setIsochrones(routing.isochrones, None)
			else:
				self.selectedRouting = None

	def onRoutingClick(self, item, event):
		if self.selectedRouting is not None and event.button == 3 and len(self.core.routingManager) > 0:
			menu = self.builder.get_object("routing-item-menu")
			menu.popup (None, None, None, None, event.button, event.time)
