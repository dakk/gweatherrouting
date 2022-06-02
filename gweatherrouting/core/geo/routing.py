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
import gpxpy
from . import Track

class Routing (Track):
	# def __init__(self, name, points = [], visible = True, collection = None):
	# 	super().__init__(name, points, visible, collection)

	def toGPXObject(self):
		gpx_route = gpxpy.gpx.GPXRoute()

		for x in self.waypoints:
			gpx_route.points.append(gpxpy.gpx.GPXRoutePoint(x[0], x[1]))

		return gpx_route
