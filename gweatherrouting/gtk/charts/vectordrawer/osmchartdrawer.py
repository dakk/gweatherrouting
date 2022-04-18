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


symbols = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath(os.path.dirname(__file__)) + '/../../../data/rastersymbols-day.png')

SYMBOL_MAP = {
	# 'name': [x, y, w, h]
	'cape': [31*28, 28*3, 28, 28],
	'harbour': [28*33+16, 28*8+16, 28, 28],
	'anchorage': [28*2, 28*12+16, 28, 28],
	'wreck': [28, 28*12+16, 28, 28],
	'fuel': [28*10 - 8, 28*17+16, 28, 28],

	'light-red': [28*9-8, 28*6, 28, 28],
	'light-green': [28*10-8, 28*7, 28, 28],
	'light-yellow': [28*10-8, 28*6, 28, 28],
	'light-generic': [28*9-8, 28*7, 28, 28],
}


def drawSymbol (cr, n, xx, yy):
	x, y, w, h = SYMBOL_MAP[n]
	img = symbols.new_subpixbuf(x, y, w, h)
	Gdk.cairo_set_source_pixbuf(cr, img, xx-14, yy-14)
	cr.paint()


def drawLight (cr, xx, yy, tags, major=False):
	cr.move_to(xx + 12, yy + 4)
	try:
		txt = tags['seamark:light:character'] + '.' + tags['seamark:light:colour'][0].upper() + '.' + tags['seamark:light:period'] + 's'
		cr.show_text(txt)
	except:
		y = yy + 4
		i = 1
		while True:
			try:
				txt = tags['seamark:light:'+str(i)+':character'] + '.' + tags['seamark:light:'+str(i)+':colour'][0].upper() + '.' + tags['seamark:light:'+str(i)+':period'] + 's'
			except:
				break
			cr.move_to(xx + 12, y)
			cr.show_text(txt)
			y += 12
			i += 1
	
	x, y, w, h = SYMBOL_MAP['light-yellow']
	img = symbols.new_subpixbuf(x, y, w, h)
	Gdk.cairo_set_source_pixbuf(cr, img, xx-14, yy-14)
	cr.paint()


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
			if scale > 100: 
				return

			cr.move_to(xx + 8, yy + 4)
			cr.show_text(name)

			drawSymbol(cr, 'cape', xx, yy)
				
		# HARBOUR
		elif 'seamark:type' in tags and tags['seamark:type'] == 'harbour':
			if scale > 100: 
				return
			
			cr.move_to(xx + 8, yy + 4)
			cr.show_text(name)

			drawSymbol(cr, 'harbour', xx, yy)

		# ANCHORAGE
		elif 'seamark:type' in tags and tags['seamark:type'] == 'anchorage':
			if scale > 100: 
				return

			drawSymbol(cr, 'anchorage', xx, yy)

		# WRECK
		elif 'seamark:type' in tags and tags['seamark:type'] == 'wreck':
			if scale > 100: 
				return

			drawSymbol(cr, 'wreck', xx, yy)

		# FUEL
		elif 'seamark:type' in tags and tags['seamark:type'] == 'small_craft_facility' and 'seamark:small_craft_facility:category' in tags and tags['seamark:small_craft_facility:category'] == 'fuel_station':
			if scale > 100: 
				return
				
			# drawSymbol(cr, 'fuel', xx, yy)

		# MINOR LIGHT
		elif 'seamark:type' in tags and tags['seamark:type'] == 'light_minor':
			if scale > 100: 
				return

			ln = 'generic'

			if 'seamark:light:colour' in tags:
				if tags['seamark:light:colour'] == 'red':
					ln = 'red'
				elif tags['seamark:light:colour'] == 'green':
					ln = 'green'
				elif tags['seamark:light:colour'] == 'yellow':
					ln = 'yellow'

			drawSymbol(cr, 'light-' + ln, xx, yy)


		# MAJOR LIGHT
		elif 'seamark:type' in tags and tags['seamark:type'] == 'light_major':
			if scale > 400: 
				return

			drawLight(cr, xx, yy, tags, True)
		# else:
		# 	print (name)
		# 	print (tags)
