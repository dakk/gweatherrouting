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
import math
import json
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gtk, Gio, GObject, OsmGpsMap
from .vectorchartdrawer import VectorChartDrawer


class GeoJSONChartDrawer(VectorChartDrawer):
	def draw(self, gpsmap, cr, vectorFile, bounding):
		self.backgroundRender(gpsmap, cr)

		for i in range(vectorFile.GetLayerCount()):
			layer = vectorFile.GetLayerByIndex(i)
			layer.SetSpatialFilter(bounding)

			# Iterate over features
			feat = layer.GetNextFeature()
			while feat is not None:
				feat = layer.GetNextFeature()

				if not feat:
					continue 

				self.featureRender(gpsmap, cr, feat, layer)

	def backgroundRender(self, gpsmap, cr):
		width = float(gpsmap.get_allocated_width())
		height = float(gpsmap.get_allocated_height())
		cr.set_source_rgba(32 / 255, 125 / 255, 150 / 255, 1.0)
		cr.rectangle(0, 0, width, height)
		cr.stroke_preserve()
		cr.fill()

	def featureRender(self, gpsmap, cr, feat, layer):
		geom = feat.GetGeometryRef()
		gj = json.loads(geom.ExportToJson())

		cr.set_line_width(1)

		if gj["type"] == "Polygon":
			for l in gj["coordinates"]:
				cr.set_source_rgba(245 / 255.0, 203 / 255.0, 66 / 255.0, 1.0)
				for x in l:
					xx, yy = gpsmap.convert_geographic_to_screen(
						OsmGpsMap.MapPoint.new_degrees(x[1], x[0])
					)
					cr.line_to(xx, yy)

				cr.close_path()
				cr.stroke_preserve()
				cr.set_source_rgba(245 / 255.0, 203 / 255.0, 66 / 255.0, 0.6)
				cr.fill()

		elif gj["type"] == "MultiPolygon":
			for l in gj["coordinates"]:
				for y in l:
					cr.set_source_rgba(245 / 255.0, 203 / 255.0, 66 / 255.0, 1.0)
					for x in y:
						xx, yy = gpsmap.convert_geographic_to_screen(
							OsmGpsMap.MapPoint.new_degrees(x[1], x[0])
						)
						cr.line_to(xx, yy)

					cr.close_path()
					cr.stroke_preserve()
					cr.set_source_rgba(245 / 255.0, 203 / 255.0, 66 / 255.0, 0.6)
					cr.fill()

		elif gj["type"] == "LineString":
			for x in gj["coordinates"]:
				cr.set_source_rgba(245 / 255.0, 203 / 255.0, 66 / 255.0, 1.0)
				xx, yy = gpsmap.convert_geographic_to_screen(
					OsmGpsMap.MapPoint.new_degrees(x[1], x[0])
				)
				cr.line_to(xx, yy)

			cr.close_path()
			cr.stroke_preserve()
			cr.set_source_rgba(245 / 255.0, 203 / 255.0, 66 / 255.0, 0.6)
			cr.fill()

		else:
			pass
			# print (gj['type'])
