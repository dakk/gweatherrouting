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
import os
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gio, GObject, OsmGpsMap, GdkPixbuf
from .vectorchartdrawer import VectorChartDrawer

class S57SymbolProvider:
	def __init__(self, settingsManager):
		self.settingsManager = settingsManager
		self.symbols = {}
		settingsManager.register_on_change('chartPalette', self.onChartPaletteChanged)

		self.p_day = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath(os.path.dirname(__file__)) + '/../../../data/s57/rastersymbols-day.png')
		self.p_dark = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath(os.path.dirname(__file__)) + '/../../../data/s57/rastersymbols-dark.png')

		self.p_select = self.p_day

	def onChartPaletteChanged(self, v):
		self.palette = v
		if v == 'dark':
			self.p_select = self.p_dark
		else:
			self.p_select = self.p_day


class S57ChartDrawer(VectorChartDrawer):
	def draw(self, gpsmap, cr, vectorFile, bounding):
		for i in range(vectorFile.GetLayerCount()):
			layer = vectorFile.GetLayerByIndex(i)
			layer.SetSpatialFilter(bounding)

			print (i, layer.GetName())

			# Iterate over features
			feat = layer.GetNextFeature()
			while feat is not None:
				feat = layer.GetNextFeature()

				if not feat:
					continue 

				# print (feat.GetFieldCount())
				for x in range(feat.GetFieldCount()):
					fd = feat.GetFieldDefnRef(x)

					# print (fd.GetNameRef())

				geom = feat.GetGeometryRef()
				# print (geom)

				# gj = json.loads(geom.ExportToJson())

				# cr.set_line_width(1)

				# if gj["type"] == "Polygon":
				# 	for l in gj["coordinates"]:
				# 		cr.set_source_rgba(245 / 255.0, 203 / 255.0, 66 / 255.0, 1.0)
				# 		for x in l:
				# 			xx, yy = gpsmap.convert_geographic_to_screen(
				# 				OsmGpsMap.MapPoint.new_degrees(x[1], x[0])
				# 			)
				# 			cr.line_to(xx, yy)

				# 		cr.close_path()
				# 		cr.stroke_preserve()
				# 		cr.set_source_rgba(245 / 255.0, 203 / 255.0, 66 / 255.0, 0.6)
				# 		cr.fill()
				# return