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
				# try:
				self.featureRender(gpsmap, cr, geom, feat, layer)
				# except Exception as e:
				# 	print('Failed to render OSM feature:', e)

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

			self.symbolProvider.draw(cr, 'HILTOP01', xx, yy)
				
		# HARBOUR
		elif 'seamark:type' in tags and tags['seamark:type'] == 'harbour':
			if scale > 100: 
				return
			
			cr.move_to(xx + 8, yy + 4)
			cr.show_text(name)

			self.symbolProvider.draw(cr, 'SMCFAC02', xx, yy)

		# ANCHORAGE
		elif 'seamark:type' in tags and tags['seamark:type'] == 'anchorage':
			if scale > 100: 
				return

			self.symbolProvider.draw(cr, 'ACHARE02', xx, yy)

		# WRECK
		elif 'seamark:type' in tags and tags['seamark:type'] == 'wreck':
			if scale > 100: 
				return

			self.symbolProvider.draw(cr, 'WRECKS01', xx, yy)

		# FUEL
		elif 'seamark:type' in tags and tags['seamark:type'] == 'small_craft_facility' and 'seamark:small_craft_facility:category' in tags and tags['seamark:small_craft_facility:category'] == 'fuel_station':
			if scale > 100: 
				return
				
			# self.symbolProvider.draw(cr, 'fuel', xx, yy)

		# MINOR LIGHT
		elif 'seamark:type' in tags and (tags['seamark:type'] == 'light_minor' or tags['seamark:type'] == 'beacon_special_purpose'):
			if scale > 100: 
				return

			ln = 'BCNSTK62'

			if 'seamark:light:colour' in tags:
				if tags['seamark:light:colour'].lower() == 'red':
					ln = 'BOYLAT14'
				elif tags['seamark:light:colour'].lower() == 'green':
					ln = 'BOYLAT13'

			self.symbolProvider.draw(cr, ln, xx, yy)


		# ROCK
		elif 'seamark:type' in tags and tags['seamark:type'] == 'rock':
			if scale > 400: 
				return

			s = 'UWTROC03'

			if 'seamark:rock:water_level' in tags:
				if tags['seamark:rock:water_level'] == 'awash':
					s = 'UWTROC03'
				if tags['seamark:rock:water_level'] == 'covers':
					s = 'UWTROC04'

			self.symbolProvider.draw(cr, s, xx, yy)

		# ISOLATE DANGER
		elif 'seamark:type' in tags and tags['seamark:type'] == 'buoy_isolated_danger':
			if scale > 100: 
				return

			self.symbolProvider.draw(cr, 'BOYCAN76', xx, yy)

		# SPECIAL PURPOSE
		elif 'seamark:type' in tags and tags['seamark:type'] == 'buoy_special_purpose':
			if scale > 100: 
				return

			self.symbolProvider.draw(cr, 'BOYSPP11', xx, yy)


		# MAJOR LIGHT
		elif 'seamark:type' in tags and tags['seamark:type'] == 'light_major':
			if scale > 600: 
				return

			self.symbolProvider.drawLight(cr, xx, yy, tags, True)

		# BEACON CARDINAL / BUOY CARDINAL
		elif 'seamark:type' in tags and (tags['seamark:type'] == 'beacon_cardinal' or tags['seamark:type'] == 'buoy_cardinal'):
			if scale > 100: 
				return

			dir = tags['seamark:beacon_cardinal:category'][0].lower()

			if dir == 'n':
				c = 'BCNCAR01'
			elif dir == 's':
				c = 'BCNCAR03'
			elif dir == 'e':
				c = 'BCNCAR02'
			elif dir == 'w':
				c = 'BCNCAR04'

			if 'seamark:name' in tags:
				cr.move_to(xx + 8, yy)
				cr.show_text(tags['seamark:name'])

			self.symbolProvider.draw(cr, c, xx, yy)


		# BEACON LATERAL / BUOY LATERAL
		elif 'seamark:type' in tags and (tags['seamark:type'] == 'beacon_lateral' or tags['seamark:type'] == 'buoy_lateral'):
			if scale > 100: 
				return

			ln = 'BCNSTK62'

			if 'seamark:beacon_lateral:category' in tags:
				if tags['seamark:beacon_lateral:category'] == 'port':
					ln = 'BOYLAT14'
				elif tags['seamark:beacon_lateral:category'] == 'starboard':
					ln = 'BOYLAT13'
			elif 'seamark:light:colour' in tags:
				if tags['seamark:light:colour'].lower() == 'red':
					ln = 'BOYLAT14'
				elif tags['seamark:light:colour'].lower() == 'green':
					ln = 'BOYLAT13'

			self.symbolProvider.draw(cr, ln, xx, yy)

		# else:
		# 	print (name)
		# 	print (tags)
