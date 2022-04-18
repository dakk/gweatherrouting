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
import os
import json
from osgeo import ogr, osr, gdal

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gdk, Gio, GObject, OsmGpsMap, GdkPixbuf
from .vectorchartdrawer import VectorChartDrawer
from ...style import *


class OSMChartDrawer(VectorChartDrawer):
	def __init__(self, settingsManager):
		super().__init__(settingsManager)

		# Load file rastersymbols-day.png
		self.symbols = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath(os.path.dirname(__file__)) + '/../../../data/rastersymbols-day.png')


	def draw(self, gpsmap, cr, vectorFile, bounding):
		for i in range(vectorFile.GetLayerCount()):
			layer = vectorFile.GetLayerByIndex(i)
			layer.SetSpatialFilter(bounding)

			# Iterate over features
			feat = layer.GetNextFeature()
			while feat is not None:
				if not feat:
					continue 

				geom = feat.GetGeometryRef()
				self.featureRender(gpsmap, cr, geom, feat, layer)
				feat = layer.GetNextFeature()


	def featureRender(self, gpsmap, cr, geom, feat, layer):
		tags = {}
		name = None 

		for i in range (feat.GetFieldCount()):
			f = feat.GetFieldDefnRef(i)

			if f.GetNameRef() == 'name':
				name = feat.GetFieldAsString(i)
			if f.GetNameRef() == 'other_tags':
				tt = feat.GetFieldAsString(i).split('"')

				k = None 

				for x in tt:
					if x == '=>' or x == '' or x == ',':
						continue

					if k == None:
						k = x 
						continue
						
					tags[k] = x
					k = None

		pt = geom.GetPoint(0)
		xx, yy = gpsmap.convert_geographic_to_screen(OsmGpsMap.MapPoint.new_degrees(pt[1], pt[0]))	
		
		scale = gpsmap.get_scale()
		cr.set_source_rgba(0, 0, 0, 0.8)
		cr.set_font_size(9)
		cr.move_to(xx, yy)

		# CAPE
		if 'natural' in tags and tags['natural'] == 'cape':
			if scale > 200: 
				return

			cr.move_to(xx + 8, yy + 4)
			cr.show_text(name)

			img = self.symbols.new_subpixbuf(31*28, 28*3, 28, 28)
			Gdk.cairo_set_source_pixbuf(cr, img, xx-14, yy-14)
			cr.paint()
				
		# HARBOUR
		elif 'seamark:type' in tags and tags['seamark:type'] == 'harbour':
			if scale > 200: 
				return
			
			cr.move_to(xx + 8, yy + 4)
			cr.show_text(name)

			img = self.symbols.new_subpixbuf(0, 0, 28, 28)
			Gdk.cairo_set_source_pixbuf(cr, img, xx-14, yy-14)
			cr.paint()

		# ANCHORAGE
		elif 'seamark:type' in tags and tags['seamark:type'] == 'anchorage':
			if scale > 200: 
				return

			img = self.symbols.new_subpixbuf(28*3, 0, 28, 28)
			Gdk.cairo_set_source_pixbuf(cr, img, xx-14, yy-14)
			cr.paint()

		# MINOR LIGHT
		elif 'seamark:type' in tags and tags['seamark:type'] == 'light_minor':
			if scale > 200: 
				return

			if 'seamark:light:colour' in tags:
				if tags['seamark:light:colour'] == 'red':
					img = self.symbols.new_subpixbuf(28*9, 28*6, 28, 28)
				elif tags['seamark:light:colour'] == 'green':
					img = self.symbols.new_subpixbuf(28*10, 28*7, 28, 28)
				else:
					img = self.symbols.new_subpixbuf(28*9, 28*6, 28, 28)
			else:
				img = self.symbols.new_subpixbuf(28*9, 28*6, 28, 28)

			Gdk.cairo_set_source_pixbuf(cr, img, xx-14, yy-14)
			cr.paint()

		else:
			print (name)
			print (tags)
