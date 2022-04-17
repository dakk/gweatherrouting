# -*- coding: utf-8 -*-
# Copyright (C) 2017-2022 Davide Gessa
"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

For detail about GNU see <http://www.gnu.org/licenses/>.
"""

import gi
import math
import json

from gweatherrouting.gtk.charts.cm93driver import CM93Driver
from .vectordrawer import SimpleChartDrawer
from .vectordrawer import S57ChartDrawer
from .vectordrawer import CM93ChartDrawer
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap
from .chartlayer import ChartLayer

class GDALVectorChart(ChartLayer):
	def __init__(self, path, settingsManager, metadata = None):
		super().__init__(path, 'vector', settingsManager, metadata)

		self.drawer = None 

		drvName = None
		if path.find("geojson") != -1:
			drvName = "GeoJSON"
			self.drawer = SimpleChartDrawer()
		elif path.find("shp") != -1:
			drvName = "ESRI Shapefile"
			self.drawer = SimpleChartDrawer()
		elif path.find (".000") != -1:
			drvName = "S57"
			self.drawer = S57ChartDrawer()
		elif path.find ("Cm93") != -1:
			drvName = "CM93"
			self.drawer = CM93ChartDrawer()

		if drvName == None and self.drawer == None:
			raise ("Invalid format")

		if drvName == 'CM93':
			drv = CM93Driver()
		else:
			drv = ogr.GetDriverByName(drvName)			
		self.vectorFile = drv.Open(path)

		if self.vectorFile == None:
			raise ("Unable to open vector map %s" % path)

	def onRegister(self, onTickHandler = None):
		pass

	def do_draw(self, gpsmap, cr):
		boundingGeometry = self.getBoundingGeometry(gpsmap)
		self.drawer.draw(gpsmap, cr, self.vectorFile, boundingGeometry)

	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False

