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

from gweatherrouting.core.dummy_storage import DATA_DIR
from gweatherrouting.gtk.charts.gshhs import GSHHSAskDownloadDialog, GSHHSDownloadDialog, GSHHSVectorChart

from ... import log
import logging
from .chartlayer import ChartLayer
from .gdalvectorchart import GDALVectorChart
from .gdalrasterchart import GDALRasterChart

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, Gdk

from osgeo import ogr, osr, gdal
from gweatherrouting.core.storage import DATA_DIR


logger = logging.getLogger ('gweatherrouting')

class ChartManager(GObject.GObject, OsmGpsMap.MapLayer):
	def __init__(self):
		GObject.GObject.__init__(self)
		self.charts = []

	def loadBaseChart(self, parent):
		if os.path.exists(DATA_DIR + "/gshhs"):
			self.charts = [GSHHSVectorChart(DATA_DIR + "/gshhs")] + self.charts
			return True

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
					self.loadBaseChart(parent, self)
			else:
				self.charts = [GDALVectorChart(os.path.abspath(os.path.dirname(__file__)) + "/../../data/countries.geojson")] + self.charts

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
