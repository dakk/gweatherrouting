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
from .geojsonchartdrawer import GeoJSONChartDrawer
from .s57chartdrawer import S57ChartDrawer
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.0')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

class GDALVectorChart:
	def __init__(self, path, drvName = None):
		self.drawer = None 

		if drvName == None:
			if path.find("geojson") != -1:
				drvName = "GeoJSON"
				self.drawer = GeoJSONChartDrawer()
			elif path.find("shp") != -1:
				drvName = "ESRI Shapefile"
			elif path.find (".000") != -1:
				drvName = "S57"
				self.drawer = S57ChartDrawer()
		else:
			if drvName == 'S57':
				self.drawer = S57ChartDrawer()
			elif drvName == 'GeoJSON':
				self.drawer = GeoJSONChartDrawer()

		if drvName == None or self.drawer == None:
			raise ("Invalid format")

		drv = ogr.GetDriverByName(drvName)
		
		self.vectorFile = drv.Open(path)

		if self.vectorFile == None:
			raise ("Unable to open vector map %s" % path)



	def do_draw(self, gpsmap, cr):
		# Get bounding box
		p1, p2 = gpsmap.get_bbox()

		## TODO: this is wrong since some countries are not renderized correctly
		p1lat, p1lon = p1.get_degrees()
		p2lat, p2lon = p2.get_degrees()
		wktbb = "POLYGON((%f %f,%f %f,%f %f,%f %f,%f %f))" % (
			p1lon,
			p1lat,
			p1lon,
			p2lat,
			p2lon,
			p2lat,
			p2lon,
			p1lat,
			p1lon,
			p1lat
		)

		self.drawer.draw(gpsmap, cr, self.vectorFile, ogr.CreateGeometryFromWkt(wktbb))


	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False

