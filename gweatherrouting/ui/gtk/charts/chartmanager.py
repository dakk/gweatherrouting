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

from .gdalvectorchart import GDALVectorChart
from .gdalrasterchart import GDALRasterChart

gi.require_version("Gtk", "3.0")
gi.require_version("OsmGpsMap", "1.2")

from gi.repository import Gtk, Gio, GObject, OsmGpsMap


class ChartLayer:
	def __init__(self, layer, path, ctype = 'vector', enabled = True):
		self.layer = layer
		self.path = path
		self.ctype = ctype
		self.enabled = enabled

class ChartManager(GObject.GObject, OsmGpsMap.MapLayer):
	def __init__(self, m):
		GObject.GObject.__init__(self)

		self.map = m
		self.charts = {}

	def loadBaseChart(self):
		self.charts["countries.geojson"] = ChartLayer(
			GDALVectorChart(os.path.abspath(os.path.dirname(__file__)) + "/../../../data/countries.geojson"),
			os.path.abspath(os.path.dirname(__file__)) + "/../../../data/countries.geojson"
		)

		# self.charts["test"] = ChartLayer(
		# 	GDALRasterChart("/run/media/dakk/e6a53908-e899-475e-8a2c-134c0e394aeb/Maps/kap/L10-368-520-8-24_10.kap"),
		# 	"/run/media/dakk/e6a53908-e899-475e-8a2c-134c0e394aeb/Maps/kap/L10-368-520-8-24_10.kap"
		# )

		# self.charts["s57test"] = ChartLayer(
		#     GDALVectorChart('/home/dakk/ENC_ROOT/US2EC03M/US2EC03M.000', 'S57'),
		# 	'/home/dakk/ENC_ROOT/US2EC03M/US2EC03M.000'
		# )


	def loadVectorLayer(self, path):
		pass

	def loadRasterLayer(self, path):
		pass

	def removeLayer(self, name):
		del self.charts[name]

	def do_draw(self, gpsmap, cr):
		for x in self.charts:
			if self.charts[x].enabled:
				self.charts[x].layer.do_draw(gpsmap, cr)

	def do_render(self, gpsmap):
		for x in self.charts:
			if self.charts[x].enabled:
				self.charts[x].layer.do_render(gpsmap)

	def do_busy(self):
		for x in self.charts:
			if self.charts[x].enabled:
				self.charts[x].layer.do_busy()

	def do_button_press(self, gpsmap, gdkeventbutton):
		for x in self.charts:
			if self.charts[x].enabled:
				self.charts[x].layer.do_button_press(gpsmap, gdkeventbutton)


GObject.type_register(ChartManager)
