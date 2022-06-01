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
import logging
import os
import gi

gi.require_version("Gtk", "3.0")
try:
	gi.require_version('OsmGpsMap', '1.2')
except:
	gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, GObject, OsmGpsMap, Gdk

from ...core.core import LinePointValidityProvider
from ...core.storage import DATA_DIR
from .gshhs import GSHHSAskDownloadDialog, GSHHSDownloadDialog, GSHHSVectorChart, OSMAskDownloadDialog, OSMDownloadDialog

from .gdalvectorchart import GDALVectorChart
from .gdalrasterchart import GDALRasterChart

logger = logging.getLogger ('gweatherrouting')

class ChartManager(GObject.GObject, OsmGpsMap.MapLayer):
	def __init__(self, settingsManager):
		GObject.GObject.__init__(self)
		self.charts = []
		self.gshhsLayer = None
		self.osmLayer = None
		self.settingsManager = settingsManager

		self.settingsManager.register_on_change('chartPalette', self.onChartPaletteChanged)

	def getLinePointValidityProviders(self):
		lpvp = []
		for x in filter(lambda x: x.enabled, self.charts):
			if isinstance(x, LinePointValidityProvider):
				lpvp += [x]
		return lpvp

	def onChartPaletteChanged(self, v):
		# self.queue_draw ()
		# TODO QUEUE A DRAW
		pass

	def loadBaseChart(self, parent):
		if os.path.exists(DATA_DIR + "/gshhs"):
			self.gshhsLayer = GSHHSVectorChart(DATA_DIR + "/gshhs", self.settingsManager)
			self.charts = [self.gshhsLayer] + self.charts
			gshhs = True

		if os.path.exists(DATA_DIR + "/seamarks.pbf"):
			self.osmLayer = GDALVectorChart(DATA_DIR + "/seamarks.pbf", self.settingsManager)
			self.charts = self.charts + [self.osmLayer]
			osm = True

		if not self.gshhsLayer:
			logger.info("GSHHS files not found, open a dialog asking for download")

			def f():
				Gdk.threads_enter()
				d = GSHHSAskDownloadDialog(parent)
				r = d.run()
				d.destroy()
				if r == Gtk.ResponseType.OK:
					d = GSHHSDownloadDialog(parent)
					r = d.run()
					d.destroy()
					if r == Gtk.ResponseType.OK:
						self.loadBaseChart(parent)
				else:
					self.charts = [GDALVectorChart(os.path.abspath(os.path.dirname(__file__)) + "/../../data/countries.geojson", self.settingsManager)] + self.charts

				Gdk.threads_leave()

			GObject.timeout_add(10, f)

		if not self.osmLayer:
			logger.info("OSM file not found, open a dialog asking for download")

			def ff():
				Gdk.threads_enter()
				d = OSMAskDownloadDialog(parent)
				r = d.run()
				d.destroy()
				if r == Gtk.ResponseType.OK:
					d = OSMDownloadDialog(parent)
					r = d.run()
					d.destroy()
					if r == Gtk.ResponseType.OK:
						self.loadBaseChart(parent)

				Gdk.threads_leave()

			GObject.timeout_add(10, ff)

	def loadVectorLayer(self, path, metadata = None, enabled = True):
		logger.info("Loading vector chart %s", path)
		l = GDALVectorChart(path, self.settingsManager, metadata=metadata, enabled=enabled)
		self.charts += [l]

		if self.osmLayer and enabled:
			self.osmLayer.enabled = False 
		if self.gshhsLayer and enabled:
			self.gshhsLayer.forceDownscale = True

		return l

	def loadRasterLayer(self, path, metadata = None, enabled = True):
		logger.info("Loading raster chart %s", path)
		l = GDALRasterChart(path, self.settingsManager, metadata=metadata, enabled=enabled)
		self.charts += [l]

		if self.osmLayer and enabled:
			self.osmLayer.enabled = False
		if self.gshhsLayer and enabled:
			self.gshhsLayer.forceDownscale = True
		return l

	def do_draw(self, gpsmap, cr):
		for x in filter(lambda x: x.enabled, self.charts):
			x.do_draw(gpsmap, cr)

	def do_render(self, gpsmap):
		for x in filter(lambda x: x.enabled, self.charts):
			x.do_render(gpsmap)

	def do_busy(self):
		for x in filter(lambda x: x.enabled, self.charts):
			x.do_busy()

	def do_button_press(self, gpsmap, gdkeventbutton):
		for x in filter(lambda x: x.enabled, self.charts):
			x.do_button_press(gpsmap, gdkeventbutton)


GObject.type_register(ChartManager)
