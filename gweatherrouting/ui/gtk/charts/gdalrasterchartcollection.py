# -*- coding: utf-8 -*-
# Copyright (C) 2017-2021 Davide Gessa
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
import numpy
import struct
import cairo
from os import listdir
from os.path import isfile, join
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap
from .gdalrasterchart import GDALRasterChart

# https://gdal.org/tutorials/raster_api_tut.html

class GDALRasterChartCollection:
	def __init__(self, path, drvName=None):
		self.rasters = []

		for x in [f for f in listdir(path) if isfile(join(path, f))]:
			if x.find('L10') == -1:
				continue
			# try:
			print ('Loading',x)
			r = GDALRasterChart(path + x)
			self.rasters.append(r)
			# except Exception as e:
			# print ('error', str(e))


	def do_draw(self, gpsmap, cr):
		for x in self.rasters:
			x.do_draw(gpsmap, cr)

	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False
