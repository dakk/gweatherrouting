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

from .s57symbolprovider import S57SymbolProvider

gi.require_version("Gtk", "3.0")
gi.require_version('OsmGpsMap', '1.2')

from gi.repository import Gtk, Gdk, Gio, GObject, OsmGpsMap, GdkPixbuf



class VectorChartDrawer:
	def __init__(self, settingsManager):
		self.onChartPaletteChanged(settingsManager.chartPalette)
		settingsManager.register_on_change('chartPalette', self.onChartPaletteChanged)

		self.symbolProvider = S57SymbolProvider(settingsManager)

	# TODO: this will handle object queries
	def onQueryPoint(self, lat, lon):
		raise ("Not implemented")

	def onChartPaletteChanged(self, v):
		self.palette = v

	def draw(self, gpsmap, cr, vectorFile, bounding):
		raise ("Not implemented")