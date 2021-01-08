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
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gtk, Gio, GObject, OsmGpsMap

class GDALVectorChart:
	def __init__(self, path, drvName = None):
		if drvName == None:
			if path.find("geojson") != -1:
				drvName = "GeoJSON"
			elif path.find("shp") != -1:
				drvName = "ESRI Shapefile"
			elif path.find (".000") != -1:
				drvName = "S57"

		if drvName == None:
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

		# Iterate over layers
		for i in range(self.vectorFile.GetLayerCount()):
			layer = self.vectorFile.GetLayerByIndex(i)
			layer.SetSpatialFilter(ogr.CreateGeometryFromWkt(wktbb))

			# Iterate over features
			feat = layer.GetNextFeature()
			while feat is not None:
				feat = layer.GetNextFeature()

				if not feat:
					continue 

				geom = feat.GetGeometryRef()
				gj = json.loads(geom.ExportToJson())

				cr.set_source_rgba(245/255., 203/255., 66/255., 1.0)
				cr.set_line_width(1)


				if gj['type'] == 'Polygon':
					for l in gj["coordinates"]:
						for x in l:
							xx, yy = gpsmap.convert_geographic_to_screen(
								OsmGpsMap.MapPoint.new_degrees(x[1], x[0])
							)
							cr.line_to(xx, yy)

						cr.close_path()
						cr.stroke_preserve()
						cr.fill()

				elif gj['type'] == 'MultiPolygon':
					for l in gj["coordinates"]:
						for y in l:
							for x in y:
								xx, yy = gpsmap.convert_geographic_to_screen(
									OsmGpsMap.MapPoint.new_degrees(x[1], x[0])
								)
								cr.line_to(xx, yy)

							cr.close_path()
							cr.stroke_preserve()
							cr.fill()


				elif gj['type'] == 'LineString':
					for x in gj["coordinates"]:
						xx, yy = gpsmap.convert_geographic_to_screen(
							OsmGpsMap.MapPoint.new_degrees(x[1], x[0])
						)
						cr.line_to(xx, yy)

						cr.close_path()
						cr.stroke_preserve()
						cr.fill()
				
				else:
					print (gj['type'])

	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False

