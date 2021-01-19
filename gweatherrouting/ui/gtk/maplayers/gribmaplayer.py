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
import colorsys
import math

gi.require_version("Gtk", "3.0")
gi.require_version("OsmGpsMap", "1.0")

from gi.repository import Gtk, Gio, GObject, OsmGpsMap
from itertools import tee
import cairo




class GribMapLayer(GObject.GObject, OsmGpsMap.MapLayer):
	def __init__(self, gribManager, timeControl):
		GObject.GObject.__init__(self)
		self.gribManager = gribManager
		self.timeControl = timeControl
		self.timeControl.connect("time-change", self.onTimeChange)

	def onTimeChange(self, t):
		pass

	def _windColor(self, wspeed):
		color = "0000CC"
		if wspeed >= 0 and wspeed < 2:
			color = "0000CC"
		elif wspeed >= 2 and wspeed < 4:
			color = "0066FF"
		elif wspeed >= 4 and wspeed < 6:
			color = "00FFFF"
		elif wspeed >= 6 and wspeed < 8:
			color = "00FF66"
		elif wspeed >= 8 and wspeed < 10:
			color = "00CC00"
		elif wspeed >= 10 and wspeed < 12:
			color = "66FF33"
		elif wspeed >= 12 and wspeed < 14:
			color = "CCFF33"
		elif wspeed >= 14 and wspeed < 16:
			color = "FFFF66"
		elif wspeed >= 16 and wspeed < 18:
			color = "FFCC00"
		elif wspeed >= 18 and wspeed < 20:
			color = "FF9900"
		elif wspeed >= 20 and wspeed < 22:
			color = "FF6600"
		elif wspeed >= 22 and wspeed < 24:
			color = "FF3300"
		elif wspeed >= 24 and wspeed < 26:
			color = "FF0000"
		elif wspeed >= 26 and wspeed < 28:
			color = "CC6600"
		elif wspeed >= 28:
			color = "CC0000"

		a = int(color[0:2], 16) / 255.0
		b = int(color[2:4], 16) / 255.0
		c = int(color[4:6], 16) / 255.0
		return (a,b,c)

	def drawWindArrow(self, cr, x, y, wdir, wspeed):
		wdir = -math.radians(wdir)

		a, b, c = self._windColor(wspeed)
		cr.set_source_rgba(a, b, c, 0.5)

		length = 15

		cr.move_to(x, y)

		# cr.line_to (x + (wspeed / 2 * math.sin (wdir)), y + 1 * math.cos (wdir))
		cr.line_to(x + (length * math.sin(wdir)), y + (length * math.cos(wdir)))

		cr.line_to(
			x + (4 * math.sin(wdir - math.radians(30))),
			y + (4 * math.cos(wdir - math.radians(30))),
		)
		cr.move_to(x + (length * math.sin(wdir)), y + (length * math.cos(wdir)))
		cr.line_to(
			x + (4 * math.sin(wdir + math.radians(30))),
			y + (4 * math.cos(wdir + math.radians(30))),
		)

		cr.stroke()

	def do_draw(self, gpsmap, cr):
		p1, p2 = gpsmap.get_bbox()

		p1lat, p1lon = p1.get_degrees()
		p2lat, p2lon = p2.get_degrees()

		width = float(gpsmap.get_allocated_width())
		height = float(gpsmap.get_allocated_height())

		cr.set_line_width(1)
		cr.set_source_rgb(1, 0, 0)
		# print (p1lat, p1lon, p2lat, p2lon)

		bounds = (
			(min(p1lat, p2lat), min(p1lon, p2lon)),
			(max(p1lat, p2lat), max(p1lon, p2lon)),
		)
		data = self.gribManager.getWind2D(self.timeControl.time, bounds)

		if not data or len(data) == 0:
			return

		scale = int(gpsmap.get_scale() / 500.0)
		if scale < 1:
			scale = 1

		cr.set_line_width(1.5 / (math.ceil(len(data) / 60)))
		cr.set_line_width(1)

		# Draw arrows
		for x in data[::scale]:
			for y in x[::scale]:
				xx, yy = gpsmap.convert_geographic_to_screen(
					OsmGpsMap.MapPoint.new_degrees(y[2][0], y[2][1])
				)
				self.drawWindArrow(cr, xx, yy, y[0], y[1])

		# Draw gradients
		# for i in range(0, len(data) - scale, scale):
		# 	for j in range(0, len(data[i]) - scale, scale):
		# 		xx, yy = gpsmap.convert_geographic_to_screen(
		# 			OsmGpsMap.MapPoint.new_degrees(data[i][j][2][0], data[i][j][2][1])
		# 		)

		# 		try:
		# 			xx2, yy2 = gpsmap.convert_geographic_to_screen(
		# 				OsmGpsMap.MapPoint.new_degrees(data[i+scale][j+scale][2][0], data[i+scale][j+scale][2][1])
		# 			)
		# 		except:
		# 			continue 

		# 		dx = xx2-xx
		# 		dy = yy-yy2

		# 		pat = cairo.MeshPattern()
		# 		pat.begin_patch()
		# 		pat.move_to(xx, yy)
		# 		pat.line_to(dx+xx, yy)
		# 		pat.line_to(dx+xx, yy+dy)
		# 		pat.line_to(dx, yy+dy)

		# 		a, b, c = self._windColor(data[i][j][1])
		# 		pat.set_corner_color_rgba(0, a, b, c, 0.6)
		# 		a, b, c = self._windColor(data[i][j+1][1])
		# 		pat.set_corner_color_rgba(1, a, b, c, 0.6)
		# 		a, b, c = self._windColor(data[i+1][j+1][1])
		# 		pat.set_corner_color_rgba(2, a, b, c, 0.6)
		# 		a, b, c = self._windColor(data[i+1][j][1])
		# 		pat.set_corner_color_rgba(3, a, b, c, 0.6)
		# 		pat.end_patch()

		# 		cr.set_source(pat)
		# 		cr.rectangle(xx, yy, dx, dy)
		# 		cr.fill()


	def do_render(self, gpsmap):
		pass

	def do_busy(self):
		return False

	def do_button_press(self, gpsmap, gdkeventbutton):
		return False


GObject.type_register(GribMapLayer)
