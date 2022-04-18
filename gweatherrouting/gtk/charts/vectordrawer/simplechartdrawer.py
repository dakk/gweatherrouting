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
import math
import json
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap
from .vectorchartdrawer import VectorChartDrawer
from ...style import *


class SimpleChartDrawer(VectorChartDrawer):
	def draw(self, gpsmap, cr, vectorFile, bounding):
		strokeStyle=Style.chartPalettes[self.palette].LandStroke
		fillStyle=Style.chartPalettes[self.palette].LandFill
		seaStyle=Style.chartPalettes[self.palette].Sea

		self.backgroundRender(gpsmap, cr, seaStyle)

		for i in range(vectorFile.GetLayerCount()):
			layer = vectorFile.GetLayerByIndex(i)
			layer.SetSpatialFilter(bounding)

			# Iterate over features
			feat = layer.GetNextFeature()
			while feat is not None:
				if not feat:
					continue 

				self.featureRender(gpsmap, cr, feat, layer, strokeStyle, fillStyle)
				feat = layer.GetNextFeature()

	def backgroundRender(self, gpsmap, cr, seaStyle):
		width = float(gpsmap.get_allocated_width())
		height = float(gpsmap.get_allocated_height())
		seaStyle.apply(cr)
		cr.rectangle(0, 0, width, height)
		cr.stroke_preserve()
		cr.fill()

	def featureRender(self, gpsmap, cr, feat, layer, strokeStyle, fillStyle):
		geom = feat.GetGeometryRef()

		# Create a geometry from screen bounds
		(tlat, tlon) = gpsmap.convert_screen_to_geographic(0, 0).get_degrees()
		(blat, blon) = gpsmap.convert_screen_to_geographic(gpsmap.get_allocated_width(), gpsmap.get_allocated_height()).get_degrees()

		ring = ogr.Geometry(ogr.wkbLinearRing)
		ring.AddPoint(tlon, blat)
		ring.AddPoint(blon, blat)
		ring.AddPoint(blon, tlat)
		ring.AddPoint(tlon, tlat)
		ring.AddPoint(tlon, blat)

		bb = ogr.Geometry(ogr.wkbPolygon)
		bb.AddGeometry(ring)

		# Get the difference geometry
		geom = bb.Intersection(geom)

		# for i in range(0, geom.GetGeometryCount()):
		# 	strokeStyle.apply(cr)
		# 	g = geom.GetGeometryRef(i)
		# 	# if g.GetGeometryType() == ogr.wkbLinearRing:
		# 	# if g.GetGeometryName() == 'LINEARRING':
		# 	# 	g = g.GetLinearGeometry()
		# 	# 	print ('tog!')

		# 	for ii in range(0, g.GetPointCount()):
		# 		pt = g.GetPoint(ii)
		# 		xx, yy = gpsmap.convert_geographic_to_screen(OsmGpsMap.MapPoint.new_degrees(pt[1], pt[0]))						
		# 		cr.line_to(xx, yy)

		# 	cr.close_path()
		# 	cr.stroke_preserve()
		# 	fillStyle.apply(cr)
		# 	cr.fill()
		# return
		gj = json.loads(geom.ExportToJson())

		cr.set_line_width(1)

		if gj["type"] == "Polygon":
			for l in gj["coordinates"]:
				strokeStyle.apply(cr)
				for x in l:
					xx, yy = gpsmap.convert_geographic_to_screen(OsmGpsMap.MapPoint.new_degrees(x[1], x[0]))						
					cr.line_to(xx, yy)

				cr.close_path()
				cr.stroke_preserve()
				fillStyle.apply(cr)
				cr.fill()

		elif gj["type"] == "MultiPolygon":
			for l in gj["coordinates"]:
				for y in l:
					strokeStyle.apply(cr)
					for x in y:
						xx, yy = gpsmap.convert_geographic_to_screen(OsmGpsMap.MapPoint.new_degrees(x[1], x[0]))
						cr.line_to(xx, yy)

					cr.close_path()
					cr.stroke_preserve()
					fillStyle.apply(cr)
					cr.fill()

		elif gj["type"] == "LineString":
			for x in gj["coordinates"]:
				strokeStyle.apply(cr)
				xx, yy = gpsmap.convert_geographic_to_screen(OsmGpsMap.MapPoint.new_degrees(x[1], x[0]))

				cr.line_to(xx, yy)

			cr.close_path()
			cr.stroke_preserve()
			fillStyle.apply(cr)
			cr.fill()

		else:
			pass
			# print (gj['type'])
