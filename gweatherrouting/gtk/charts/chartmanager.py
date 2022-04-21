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

import gi
import os

from ...core.storage import DATA_DIR
from .gshhs import GSHHSAskDownloadDialog, GSHHSDownloadDialog, GSHHSVectorChart, OSMAskDownloadDialog, OSMDownloadDialog

import logging
from .gdalvectorchart import GDALVectorChart
from .gdalrasterchart import GDALRasterChart

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, GObject, OsmGpsMap, Gdk


logger = logging.getLogger ('gweatherrouting')

class ChartManager(GObject.GObject, OsmGpsMap.MapLayer):
	def __init__(self, settingsManager):
		GObject.GObject.__init__(self)
		self.charts = []
		self.settingsManager = settingsManager

		self.settingsManager.register_on_change('chartPalette', self.onChartPaletteChanged)

	def onChartPaletteChanged(self, v):
		# self.queue_draw ()
		# TODO QUEUE A DRAW
		pass

	def loadBaseChart(self, parent):
		gshhs = False
		osm = False 

		if os.path.exists(DATA_DIR + "/gshhs"):
			self.charts = [GSHHSVectorChart(DATA_DIR + "/gshhs", self.settingsManager)] + self.charts
			gshhs = True

		if os.path.exists(DATA_DIR + "/seamarks.pbf"):
			self.charts = self.charts + [GDALVectorChart(DATA_DIR + "/seamarks.pbf", self.settingsManager)]
			osm = True

		if not gshhs:
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

		if not osm:
			logger.info("OSM file not found, open a dialog asking for download")
			
			def f():
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

			GObject.timeout_add(10, f)

	def loadVectorLayer(self, path, metadata = None):
		logger.info("Loading vector chart %s" % path)
		l = GDALVectorChart(path, metadata)
		self.charts += [l]
		return l

	def loadRasterLayer(self, path, metadata = None):
		logger.info("Loading raster chart %s" % path)
		l = GDALRasterChart(path, metadata)
		self.charts += [l]
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
