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
import math
from kivy.graphics import (
	Canvas,
	Color,
	Line,
	MatrixInstruction,
	Mesh,
	PopMatrix,
	PushMatrix,
	Scale,
	Translate,
)
from kivy.graphics.tesselator import TYPE_POLYGONS, WINDING_ODD, Tesselator
from kivy.metrics import dp
from kivy.properties import ObjectProperty, StringProperty
from kivy.utils import get_color_from_hex

from kivy_garden.mapview.constants import CACHE_DIR
from kivy_garden.mapview.downloader import Downloader
from kivy_garden.mapview.view import MapLayer

from ..common import windColor


class TrackMapLayer(MapLayer):
	def __init__(self, trackManager, timeControl, **kwargs):
		super().__init__(**kwargs)
		self.trackManager = trackManager
		self.timeControl = timeControl
		self.timeControl.connect("time-change", self.onTimeChange)
		


	def onTimeChange(self, t):
		self.draw()


	def reposition(self):
		""" Function called when :class:`MapView` is moved. You must recalculate
		the position of your children. """
		self.draw()

	def unload(self):
		""" Called when the view want to completly unload the layer. """
		pass
	

	def draw(self):
		view = self.parent
		zoom = view.zoom
		bbox = view.get_bbox()

		p1lat, p1lon, p2lat, p2lon = bbox

		
		for tr in self.trackManager.routings:
			if not tr.visible:
				continue 

			prevx = None
			prevy = None 
			prevp = None 
			i = 0

			for p in tr.waypoints:
				i += 1
				x, y = view.get_window_xy_from(p[0], p[1], zoom)

				# if prevp == None:
				# 	Style.Track.RoutingTrackFont.apply(cr)
				# 	cr.move_to(x+10, y)
				# 	cr.show_text(tr.name)
				# 	cr.stroke()

				# # Draw boat
				# if prevp != None:    
				# 	tprev = dateutil.parser.parse(prevp[2])
				# 	tcurr = dateutil.parser.parse(p[2])

				# 	if tcurr >= self.timeControl.time and tprev < self.timeControl.time:
				# 		dt = (tcurr-tprev).total_seconds()
				# 		dl = utils.pointDistance(prevp[0], prevp[1], p[0], p[1]) / dt * (self.timeControl.time - tprev).total_seconds()
						
				# 		rp = utils.routagePointDistance (prevp[0], prevp[1], dl, math.radians(p[6]))

				# 		Style.Track.RoutingBoat.apply(cr)
				# 		xx, yy = gpsmap.convert_geographic_to_screen (OsmGpsMap.MapPoint.new_degrees (rp[0], rp[1]))
				# 		cr.arc(xx, yy, 7, 0, 2 * math.pi)
				# 		cr.fill()  

				# if prevx != None and prevy != None:
				# 	Style.Track.RoutingTrack.apply(cr)
				# 	cr.move_to (prevx, prevy)
				# 	cr.line_to (x, y)
				# 	cr.stroke()

				# Style.Track.RoutingTrackCircle.apply(cr)
				# cr.arc(x, y, 5, 0, 2 * math.pi)
				# cr.stroke()

				prevx = x
				prevy = y
				prevp = p

		for tr in self.trackManager.tracks:
			if not tr.visible:
				continue 

			active = False
			if self.trackManager.activeTrack and self.trackManager.activeTrack.name == tr.name:
				active = True

			prevx = None
			prevy = None 
			i = 0

			for p in tr.waypoints:
				i += 1
				x, y = view.get_window_xy_from(p[0], p[1], zoom)

				# if prevx == None:
				# 	if active:
				# 		Style.Track.TrackActiveFont.apply(cr)
				# 	else:
				# 		Style.Track.TrackInactiveFont.apply(cr)

				# 	cr.move_to(x-10, y-10)
				# 	cr.show_text(tr.name)
				# 	cr.stroke()

				
				# if active:
				# 	Style.Track.TrackActivePoiFont.apply(cr)
				# else:
				# 	Style.Track.TrackInactivePoiFont.apply(cr)
					
				# cr.move_to(x-4, y+18)
				# cr.show_text(str(i))
				# cr.stroke()

				# if prevx != None and prevy != None:
				# 	if active:
				# 		Style.Track.TrackActive.apply(cr)
				# 	else:
				# 		Style.Track.TrackInactive.apply(cr)

				# 	cr.move_to (prevx, prevy)
				# 	cr.line_to (x, y)
				# 	cr.stroke()

				# if active:
				# 	Style.Track.TrackActive.apply(cr)
				# else:
				# 	Style.Track.TrackInactive.apply(cr)

				# Style.resetDash(cr)

				# cr.arc(x, y, 5, 0, 2 * math.pi)
				# cr.stroke()

				prevx = x
				prevy = y