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

symbols_day = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath(os.path.dirname(__file__)) + '/../../../data/rastersymbols-day.png')
symbols_dark = GdkPixbuf.Pixbuf.new_from_file(os.path.abspath(os.path.dirname(__file__)) + '/../../../data/rastersymbols-dark.png')

symbols = symbols_day

SYMBOL_MAP = {
	# 'name': [x, y, w, h]
	'cape': [31*28, 28*3, 28, 28],
	'harbour': [28*33+16, 28*8+16, 28, 28],
	'anchorage': [28*2, 28*12+16, 28, 28],
	'wreck': [28, 28*12+16, 28, 28],
	'fuel': [28*10 - 8, 28*17+16, 28, 28],

	'light-minor-red': [28*4-8, 28*27+16, 28, 28],
	'light-minor-green': [28*5-12, 28*27+16, 28, 28],

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


class VectorChartDrawer:
	def __init__(self, settingsManager):
		self.onChartPaletteChanged(settingsManager.chartPalette)
		settingsManager.register_on_change('chartPalette', self.onChartPaletteChanged)

	# TODO: this will handle object queries
	def onQueryPoint(self, lat, lon):
		raise ("Not implemented")

	def onChartPaletteChanged(self, v):
		self.palette = v
		if v == 'dark':
			symbols = symbols_dark
		else:
			symbols = symbols_day

	def draw(self, gpsmap, cr, vectorFile, bounding):
		raise ("Not implemented")